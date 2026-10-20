import typing
import copy
import json
import time
import asyncio
import math
import inspect
import RPi.GPIO as pio
import threading
from .containers import Plate, Reagent_Mix
from .method_library_class import MethodLibrary
from ..db import get_db
from .kinematics import solve_5bar_FK, solve_5bar_IK, Vec2d, Vec3d, Vec2d_Ang
from . import coms as slib
from .coms import packet
from .coms import codex
from .utils import liq_handling_data, get_reagent, get_pump_id


class Machine:
    pass


class Kinematic_State():
    def __init__(self,
                 cartesian_position: Vec2d | Vec3d = Vec3d([0, 0, 0]),
                 angular_position: Vec2d_Ang | None = None):
        self.iksolved = angular_position is None
        self.fksolved = cartesian_position.x != 0 or cartesian_position.y != 0
        self.angular_position = angular_position
        self.position = cartesian_position
        if type(cartesian_position) is Vec2d:
            cartesian_position = Vec3d([*cartesian_position.axis, 0])

    def __repr__(self):
        return f"""{self.position.x}, {self.position.y}, {self.position.z}
                   {math.degrees(self.angular_position.a)},{math.degrees(self.angular_position.b)}
                   """

    def __add__(self, other):
        if isinstance(other, Vec3d):
            new = Kinematic_State(self.position + other)
            return new
        elif isinstance(other, list):
            new = Kinematic_State(Vec3d(other) + self.position)
            return new
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Vec3d):
            new = Kinematic_State(self.position - other)
            return new
        elif isinstance(other, list):
            new = Kinematic_State(self.position - Vec3d(other))
            return new
        else:
            return NotImplemented

    def __mul__(self, other):
        return NotImplemented


class Machine:
    def __init__(self, settings_path, method_library):
        self.settings_path = settings_path

        self.current_position = Kinematic_State()
        self.home_offset = Kinematic_State()
        self.aspiration_depth_offset = -10

        self.methods: MethodLibrary = method_library
        self.methods.machine = self

        self.position_known = False
        self.got_home_complete = threading.Event()
        self.move_complete = threading.Event()
        self.got_packet = threading.Event()
        self.in_simulation = False
        self.coms: slib.ComsChannel

        self.named_positions = {"waste": None}
        self.named_containers = {"waste": Reagent_Mix()}
        self.current_container = self.named_containers["waste"]

        mach = self.settings()["machine"]
        spr = mach["motors"]["common_settings"]["kinematic_steps_per_revolution"]
        pitch = mach["machineDimensions"]["z_screw_pitch"]
        self.a_steps_per_rad = spr / (2 * math.pi)
        self.b_steps_per_rad = spr / (2 * math.pi)
        self.z_steps_per_mm = spr / pitch

        self.pump_lines = {}
        pumps = mach["motors"]["pumps"]
        for pumpid in range(0, len(pumps)):
            line_contents = Reagent_Mix()
            line_contents.gain_reagent(
                f"{get_reagent(pumpid)}", reservoir=True)
            self.pump_lines[pumpid] = [line_contents]

        self.plate = Plate(self.settings()["plates"]["standard 96"])
        self.hw_init()
        self.add_default_responses()
        self.serial_coms_thread = threading.Thread(
            target=self.coms.init_coms_handler_loop, daemon=True)
        self.serial_coms_thread.start()

    def add_default_responses(self):
        def move_response(context: slib.Loopctx):
            self.move_complete.set()

        def homing_response(context: slib.Loopctx):
            mot_position = context.current_packet.get_int_argvec()
            self.current_position = self.from_steps(*mot_position)
            self.position_known = True
            self.got_home_complete.set()

        self.coms.add_response(
            "homing_response", slib.code_dependent_true(slib.codex.HOME),
            homing_response
        )

        self.coms.add_response(
            "move_confirm", slib.code_dependent_true(slib.codex.MOVE),
            move_response
        )

    def hw_init(self):
        pio.setmode(pio.BCM)
        # reboot the pico
        pi3b_pins = self.settings()["machine"]["pins"]["on_3b_server_board"]
        pico_reset_pin = pi3b_pins["pico_reset_pin"]
        stage_enable_pin = pi3b_pins["stage_enable_pin"]
        pump_ms1 = pi3b_pins["pump_ms1"]
        pump_ms2 = pi3b_pins["pump_ms2"]

        motor_settings = self.settings()["machine"]["motors"]

        pio.setup(pico_reset_pin, pio.OUT)
        pio.setup(stage_enable_pin, pio.OUT)
        pio.setup(pump_ms1, pio.OUT)
        pio.setup(pump_ms2, pio.OUT)
        pio.output(stage_enable_pin, pio.HIGH)
        pio.output(pico_reset_pin, pio.LOW)
        time.sleep(0.1)
        pio.output(pico_reset_pin, pio.HIGH)
        time.sleep(0.1)

        pump_ms_state_dict = {
            200: (0, 0),
            400: (1, 0),
            800: (0, 1),
            1600: (1, 1)
        }
        pump_stp_per_rev = motor_settings["common_settings"]["pump_steps_per_revolution"]

        pump_ms_pinstate = pump_ms_state_dict[pump_stp_per_rev]

        pio.output(pump_ms1, pump_ms_pinstate[0])
        pio.output(pump_ms2, pump_ms_pinstate[1])

        self.coms = slib.ComsChannel(self.settings_path, timeout=3)

    def settings(self):
        with open(self.settings_path, "r") as conf:
            settings = json.load(conf)
            return settings

    def get_pos_FK(self, target: Kinematic_State) -> Kinematic_State:
        solved = solve_5bar_FK(self.settings(), target.angular_position)
        output_position = Vec3d([*solved.axes, target.position.z])
        output = Kinematic_State(output_position, target.angular_position)
        return output

    def get_pos_IK(self, target: Kinematic_State) -> Kinematic_State:
        angular_target = solve_5bar_IK(
            self.settings(), target.position)
        output = Kinematic_State(target.position, angular_target)
        return output

    def to_steps(self, pos: Kinematic_State) -> Vec3d:
        out = Vec3d([0, 0, 0])
        out.axes[codex.A_MOTOR] = math.ceil(
            pos.angular_position.a * self.a_steps_per_rad)
        out.axes[codex.B_MOTOR] = math.ceil(
            pos.angular_position.b * self.b_steps_per_rad)
        out.axes[codex.Z_MOTOR] = math.ceil(
            pos.position.z * self.z_steps_per_mm)
        return out

    def from_steps(self, a, b, z) -> Kinematic_State:
        given_pos = Kinematic_State(
            Vec3d([
                0,
                0,
                z / self.z_steps_per_mm
            ]),
            Vec2d_Ang([
                a / self.a_steps_per_rad,
                b / self.b_steps_per_rad
            ])
        )
        given_pos = self.get_pos_FK(given_pos)
        return given_pos

    def goto_pos(self, pos: Kinematic_State) -> None:
        if self.current_position == pos:
            return
        self.move_complete.clear()
        if not self.position_known:
            return
        if not self.in_simulation:
            pos = self.get_pos_IK(pos)
            steps = self.to_steps(pos)

            mot_settings = self.settings()["machine"]["motors"]

            amove = slib.packet.MoveEntity(
                codex.A_MOTOR,
                codex.TRAPEZOIDAL,
                codex.ABSOLUTE,
                steps.axes[codex.A_MOTOR],
                mot_settings["common_settings"]["arms_angular_max_velocity"],
                mot_settings["common_settings"]["arms_angular_accel"]

            )
            bmove = slib.packet.MoveEntity(
                codex.B_MOTOR,
                codex.TRAPEZOIDAL,
                codex.ABSOLUTE,
                steps.axes[codex.B_MOTOR],
                mot_settings["common_settings"]["arms_angular_max_velocity"],
                mot_settings["common_settings"]["arms_angular_accel"]

            )
            zmove = slib.packet.MoveEntity(
                codex.Z_MOTOR,
                codex.TRAPEZOIDAL,
                codex.ABSOLUTE,
                steps.axes[codex.Z_MOTOR],
                mot_settings["common_settings"]["z_max_angular_velocity"],
                mot_settings["common_settings"]["z_angular_accel"]

            )

            self.coms.queue_packet(packet.move_packet([amove, bmove, zmove]))
            self.current_position = pos

    def stall_for_confirm(self, confirm_prompt_message):
        if not self.in_simulation:
            input(f"{confirm_prompt_message}")

    def goto_named(self, target_name: str):
        if target_name in self.named_positions.keys():
            target_pos = self.named_positions[target_name]
            self.goto_pos(target_pos)
            self.current_container = self.named_containers[target_name]
            return

    def goto_well(self, wellid: str):
        abs_well_pos_2d = self.plate.get_well_abs_position(wellid)
        target_pos = Kinematic_State(
            Vec3d([*abs_well_pos_2d.axes, self.current_position.position.z]))
        self.current_container = self.plate.by_alph(wellid)
        self.goto_pos(target_pos)

    def vto_steps(self, pumpid, vol):
        settings = self.settings()["machine"]["motors"]
        pump = settings["pumps"][pumpid]
        common = settings["common_settings"]
        rad_per_step = 2 * math.pi / common["pump_steps_per_revolution"]
        ul_per_step = pump["ul_per_rad"] * rad_per_step
        ul_per_step *= pump["compensation_factor"]
        return round(vol / ul_per_step)

    def group_dispense(self, volumes: list[liq_handling_data]):
        self.move_complete.clear()
        move_data = []
        retract_move_data = []

        for liq_data in volumes:
            # simulation / audit-trail handling
            if liq_data.volume == 0:
                continue

            if liq_data.volume > 0:
                end_of_line_reagent: Reagent_Mix = self.pump_lines[liq_data.pumpid][-1]

                self.current_container.gain_mixed_volume(
                    end_of_line_reagent.release_volume(liq_data.volume))

                if end_of_line_reagent.get_total_volume() == 0:
                    self.pump_lines.pop()
            else:
                self.pump_lines[liq_data.pumpid].append(
                    Reagent_Mix({"air_from_airgap_induced_by_negative_volume_dispense_call": liq_data.volume}))

            pump = self.settings()[
                "machine"]["motors"]["pumps"][liq_data.pumpid]

            disp_step_total = self.vto_steps(liq_data.pumpid,
                                             pump["droplet_vol_ul"] +
                                             pump["airgap_vol_ul"] +
                                             liq_data.volume)

            move_data.append(packet.MoveEntity(
                codex.PUMP(liq_data.pumpid),
                codex.NO_DECEL,
                codex.RELATIVE,
                disp_step_total,
                pump["ang_v_max"],
                pump["ang_accel_rad"]
            ))

            retract_move_data.append(packet.MoveEntity(
                codex.PUMP(liq_data.pumpid),
                codex.NO_DECEL,
                codex.RELATIVE,
                self.vto_steps(liq_data.pumpid,
                               - pump["droplet_vol_ul"]
                               - pump["airgap_vol_ul"]),
                pump["ang_v_max"],
                pump["ang_accel_rad"]
            ))

        self.coms.queue_packet(packet.move_packet(move_data))
        self.coms.queue_packet(packet.move_packet(retract_move_data))

    def dispense(self, volume, reagent=None, pumpid=None):
        self.group_dispense(
            [liq_handling_data(volume, pumpid=pumpid, reagent=reagent)])

    def aspirate(self, volume, pumpid):
        self.move_complete.clear()
        if volume == 0:
            return
        if volume < 0:
            raise ValueError(
                "attempting to aspirate negative volume (which would be a dispense move), fix unintended (-) sign or use dispense functions")
            return

        if not self.in_simulation:
            pump = self.settings()["machine"]["motors"]["pumps"][pumpid]
            self.goto_pos(self.current_position +
                          [0, 0, self.aspiration_depth_offset])

            self.coms.queue_packet(packet.move_packet([packet.MoveEntity(
                codex.PUMP(pumpid),
                codex.NO_DECEL,
                codex.RELATIVE,
                self.vto_steps(pumpid, -volume),
                pump["ang_v_max"],
                pump["ang_accel_rad"]
            )]))

            self.goto_pos(self.current_position +
                          [0, 0, -self.aspiration_depth_offset])

            self.coms.queue_packet(packet.move_packet([packet.MoveEntity(
                codex.PUMP(pumpid),
                codex.NO_DECEL,
                codex.RELATIVE,
                self.vto_steps(pumpid, -pump["airgap_vol_ul"]),
                pump["ang_v_max"],
                pump["ang_accel_rad"]
            )]))

        pump_line = self.pump_lines[pumpid]
        aspirant = self.current_container.release_volume(volume)
        pump_line.append(aspirant)

    def send_home(self):
        speed_settings = self.settings(
        )["machine"]["motors"]["common_settings"]
        z_vmax = float(speed_settings["z_homing_velocity"])
        z_accel = float(speed_settings["z_angular_accel"])
        ab_vmax = float(speed_settings["arms_homing_velocity"])
        ab_accel = float(speed_settings["arms_angular_accel"])
        self.coms.queue_packet(packet.make_float_vec_packet(
            codex.HOME,
            [z_vmax,
             z_accel,
             ab_vmax,
             ab_accel]
        ))
