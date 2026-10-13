from containers import Plate, Reagent_Mix, Well
from method_library_class import MethodLibrary
import copy
import json
import time
import asyncio
from ..db import get_db
import math
import inspect
import RPi.GPIO as pio
from .kinematics import solve_5bar_FK, solve_5bar_IK, Vec2d, Vec3d, Vec2d_Ang
from . import coms as slib
from .coms import packet
from .coms import codex
import typing
from utils import liq_handling_data


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
        return f"""{self.x}, {self.y}, {self.z}
                   {math.degrees(self.alpha)},{math.degrees(self.beta)}
                   """

    def __add__(self, other):
        if isinstance(other, Vec3d):
            new = Kinematic_State(self.position + other.position)
            return new
        elif isinstance(other, list):
            new = Kinematic_State(Vec3d(other) + self.position)
            return new
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Vec3d):
            new = Kinematic_State(self.position - other.position)
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
        self.aspiration_depth_offset = 0

        self.methods: MethodLibrary = method_library
        self.methods.machine = self

        self.position_known = False
        self.got_home_complete = asyncio.Event()
        self.move_complete = asyncio.Event()
        self.got_packet = asyncio.Event()
        self.in_simulation = False
        self.coms: slib.ComsChannel

        self.named_positions = {"waste": None}
        self.named_containers = {"waste": Well()}
        self.current_container = self.named_containers["waste"]

        mach = self.settings()["machine"]
        spr = mach["motors"]["common_settings"]["kinematic_steps_per_revolution"]
        pitch = mach["machineDimensions"]["z_screw_pitch"]
        self.a_steps_per_rad = spr / (2 * math.pi)
        self.b_steps_per_rad = spr / (2 * math.pi)
        self.z_steps_per_mm = spr / pitch

        self.pump_line_contents = {}
        pumps = mach["motors"]["pumps"]
        for id in range(0, len(pumps)):
            line_contents = Reagent_Mix()
            line_contents.gain_reagent(
                f"{self.get_reagent(id)}", reservoir=True)
            self.pump_line_contents[id] = [line_contents]
        print(f"pump line: {self.pump_line_contents}")

        self.plate = Plate(self.settings()["plates"]["standard 96"])
        self.hw_init()
        self.add_default_responses()

        self.coms.init_coms_handler_loop()

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
        solved = solve_5bar_FK(self.settings(), target)
        output_position = Vec3d([*solved.axis, target.position.z])
        output = Kinematic_State(output_position, target.angular_position)
        return output

    def get_pos_IK(self, target: Kinematic_State) -> Kinematic_State:
        angular_target = solve_5bar_IK(
            self.settings(), target.position)
        output = Kinematic_State(target.position, angular_target)
        return output

    def to_steps(self, pos: Kinematic_State) -> Vec3d:
        return Vec3d([math.ceil(pos.alpha * self.a_steps_per_rad),
                      math.ceil(pos.beta * self.b_steps_per_rad),
                      math.ceil(pos.z * self.z_steps_per_mm)])

    def from_steps(self, a, b, z) -> Kinematic_State:
        given_pos = Kinematic_State(
            Vec3d([
                0,
                0,
                z / self.z_steps_per_rad
            ]),
            Vec2d_Ang(
                a / self.a_steps_per_rad,
                b / self.b_steps_per_rad
            )
        )
        given_pos = self.get_pos_FK(given_pos)
        return given_pos

    def goto_pos(self, pos: Kinematic_State) -> None:
        self.move_complete.clear()
        if not self.position_known:
            return
        if not self.in_simulation:
            pos = self.get_pos_IK(pos)
            steps = self.to_steps(pos)

            mot_settings = self.settings()["motors"]

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

            self.coms.send_packet(packet.move_packet([amove, bmove, zmove]))
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
        target_pos = self.plate.get_well_abs_position(wellid)
        print(f"going to {wellid} at target position: {target_pos}")
        self.current_container = self.plate.by_alph(wellid)
        self.goto_pos(target_pos)

    def handle_liquids(self, volumes: list[liq_handling_data]):
        self.move_complete.clear()
        move_data = []
        for liq_data in volumes:
            # simulation / audit-trail handling
            if liq_data.volume == 0:
                continue
            if liq_data.volume > 0:
                if liq_data.id is None:
                    id = self.get_pump_id(liq_data.reagent)
                held_volume = self.pump_line_contents[liq_data.id][-1]
                output_liquid = held_volume.release_volume(liq_data.volume)
                if held_volume.get_total_volume() == 0:
                    self.pump_line_contents.pop()
                self.current_container.gain_liquid(output_liquid)
            elif liq_data.volume < 0:
                self.impure_method_flag = True
                pump_line = self.pump_line_contents[id]
                reagent_contents = self.current_container.contents
                pump_line.append(reagent_contents)

            settings = self.settings()["motors"]
            pump = settings["pumps"]

            rad_per_step = 2 * math.pi / settings["pump_steps_per_revolution"]
            ul_per_steps = pump["ul_per_rad"] * rad_per_step
            ul_per_steps *= pump["compensation_factor"]

            def vto_steps(vol: float):
                return round(vol * ul_per_steps)

            airgap = vto_steps(pump["droplet_vol_ul"] +
                               pump["overshoot_offset_ul"])

            move_data.append(packet.MoveEntity(
                codex.PUMP(liq_data.pumpid),
                codex.NO_DECEL,
                codex.RELATIVE,
                vto_steps(liq_data.volume + airgap),
                pump["ang_accel_rad"],
                pump["ang_v_max"]

            ))

            move_data.append(packet.MoveEntity(
                codex.PUMP(liq_data.pumpid),
                codex.NO_DECEL,
                codex.RELATIVE,
                vto_steps(-pump["droplet_vol_ul"]),
                pump["ang_accel_rad"],
                pump["ang_v_max"]
            ))

        self.coms.send_packet(packet.move_packet(move_data))
