import typing
import copy
import json
import time
import asyncio
import math
import inspect
import RPi.GPIO as pio
import threading
from .containers import Plate, Reagent_Mix, Fixture
from .method_library_class import MethodLibrary
from ..db import get_db, pumpUpdate
from .kinematics import solve_5bar_FK, solve_5bar_IK, Vec2d, Vec3d, Vec2d_Ang
from . import coms as slib
from .coms import packet
from .coms import codex
from .utils import liq_handling_data, get_reagent, get_pump_id


class Machine:
    pass


class Kinematic_State:
    def __init__(self,
                 cartesian_position: Vec3d = Vec3d([0, 0, 0]),
                 angular_position: Vec2d_Ang | None = None):
        self.iksolved = angular_position is None
        self.fksolved = cartesian_position.x != 0 or cartesian_position.y != 0
        self.angular_position = angular_position
        self.position = cartesian_position

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
        self._current_position = Kinematic_State()
        self._current_container_name = "waste"
        self.home_offset = Kinematic_State()
        self.aspiration_depth_offset = -12

        self.methods: MethodLibrary = method_library
        self.methods.machine = self

        self.set_fixture("std_fixture")

        self.position_known = False
        self.got_home_complete = threading.Event()
        self.move_complete = threading.Event()
        self.got_packet = threading.Event()
        self.in_simulation = False
        self.simulation_resource_accumulator = []
        self.coms: slib.ComsChannel

        self.pump_count = len(self.settings()["machine"]["motors"]["pumps"])

        self.pump_map = {pumpid: f"unknown_reagent_of_pump{
            pumpid}" for pumpid in range(self.pump_count)}

        self.pump_lines = {pumpid: [f"unknown_reagent_of_pump{
            pumpid}"] for pumpid in range(self.pump_count)}

        self.hw_init()

        self.add_default_responses()
        self.serial_coms_thread = threading.Thread(
            target=self.coms.init_coms_handler_loop, daemon=True)
        self.serial_coms_thread.start()

    def set_pump_reagent(self, pumpid, reagent_name):
        self.pump_map[pumpid] = reagent_name
        self.pump_lines[pumpid][0] = Reagent_Mix(
            contents={reagent_name: 1},
            is_reservoir=True
        )

    @property
    def current_position(self) -> Kinematic_State:
        return self._current_position

    @current_position.setter
    def current_position(self, value: Kinematic_State):
        self._current_position = value
        if not self.in_simulation:
            print(f"current position: {self.current_position}")

    @property
    def current_container_name(self) -> str:
        return self._current_container_name

    @current_container_name.setter
    def current_container_name(self, name):
        self._current_container_name = name
        if not self.in_simulation:
            print(f"current container: {self.current_container_name}")

    @property
    def current_container(self) -> Reagent_Mix:
        out = self.fixture.get_named_container(self.current_container_name)
        if out is None:
            if self.in_simulation:
                self.fixture.add_named_container(
                    self.current_container_name, self.current_position)
                out = self.fixture.get_named_container(
                    self.current_container_name)
        return out

    def set_fixture(self, name, plate_name="standard 96"):
        settings = self.settings()
        self.fixture = Fixture(
            settings["fixtures"]["std_plate_fixture"],
            settings["plates"]["standard 96"])

    def set_plate(self, name):
        self.fixture.plate = Plate(self.settings()["plates"][name])

    def save_mutables(self):
        self.saved = {
            "position": copy.deepcopy(self.current_position),
            "fixture": copy.deepcopy(self.fixture),
            "pumps": copy.deepcopy(self.pump_map),
            "lines": copy.deepcopy(self.pump_lines),
        }

    def restore_mutables(self):
        self.current_position = self.saved["position"]
        self.fixture = self.saved["fixture"]
        self.pump_lines = self.saved["lines"]

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
        pi3b_pins = self.settings()["machine"]["pins"]["on_3b_server_board"]
        pico_reset_pin = pi3b_pins["pico_reset_pin"]
        stage_enable_pin = pi3b_pins["stage_enable_pin"]
        pump_ms1 = pi3b_pins["pump_ms1"]
        pump_ms2 = pi3b_pins["pump_ms2"]

        motor_settings = self.settings()["machine"]["motors"]

        pump_stp_per_rev = motor_settings["common_settings"]["pump_steps_per_revolution"]

        pump_ms_state_dict = {
            200: (0, 0),
            400: (1, 0),
            800: (0, 1),
            1600: (1, 1)
        }

        pump_ms_pinstate = pump_ms_state_dict[pump_stp_per_rev]
        self.coms = slib.ComsChannel(self.settings_path, timeout=3)

        # reboot the pico
        pio.setmode(pio.BCM)
        pio.setup(pico_reset_pin, pio.OUT)
        pio.setup(stage_enable_pin, pio.OUT)
        pio.setup(pump_ms1, pio.OUT)
        pio.setup(pump_ms2, pio.OUT)

        pio.output(pump_ms1, pump_ms_pinstate[0])
        pio.output(pump_ms2, pump_ms_pinstate[1])
        pio.output(stage_enable_pin, pio.HIGH)

        pio.output(pico_reset_pin, pio.LOW)
        time.sleep(0.1)
        pio.output(pico_reset_pin, pio.HIGH)
        time.sleep(0.1)

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
        mach = self.settings()["machine"]
        spr = mach["motors"]["common_settings"]["kinematic_steps_per_revolution"]
        pitch = mach["machineDimensions"]["z_screw_pitch"]
        a_steps_per_rad = spr / (2 * math.pi)
        b_steps_per_rad = spr / (2 * math.pi)
        z_steps_per_mm = spr / pitch

        out = Vec3d([0, 0, 0])
        out.axes[codex.A_MOTOR] = math.ceil(
            pos.angular_position.a * a_steps_per_rad)
        out.axes[codex.B_MOTOR] = math.ceil(
            pos.angular_position.b * b_steps_per_rad)
        out.axes[codex.Z_MOTOR] = math.ceil(
            pos.position.z * z_steps_per_mm)
        return out

    def from_steps(self, a, b, z) -> Kinematic_State:
        mach = self.settings()["machine"]
        spr = mach["motors"]["common_settings"]["kinematic_steps_per_revolution"]
        pitch = mach["machineDimensions"]["z_screw_pitch"]
        a_steps_per_rad = spr / (2 * math.pi)
        b_steps_per_rad = spr / (2 * math.pi)
        z_steps_per_mm = spr / pitch
        given_pos = Kinematic_State(
            Vec3d([0, 0, z / z_steps_per_mm]),
            Vec2d_Ang([a / a_steps_per_rad, b / b_steps_per_rad])
        )
        given_pos = self.get_pos_FK(given_pos)
        return given_pos

    def goto_pos(self, pos: Kinematic_State | Vec3d) -> None:
        if type(pos) is Vec3d:
            pos = Kinematic_State(pos)
        if self.current_position == pos:
            return
        self.move_complete.clear()
        if not self.position_known:
            return
        if self.in_simulation:
            self.current_position = pos
        else:
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

            if self.current_position.position.z < pos.position.z:
                self.coms.queue_packet(packet.move_packet([zmove]))
                self.coms.queue_packet(packet.move_packet([amove, bmove]))
            else:
                self.coms.queue_packet(packet.move_packet([amove, bmove]))
                self.coms.queue_packet(packet.move_packet([zmove]))
        self.current_position = pos

    def stall_for_confirm(self, confirm_prompt_message):
        if not self.in_simulation:
            input(f"{confirm_prompt_message}")

    def record_needed_resource(self, data):
        found_identical = False

        for record in self.simulation_resource_accumulator:
            found_identical = data == record
            if found_identical:
                break
        if not found_identical:
            self.simulation_resource_accumulator.append(data)

    def goto_named(self, target_name: str | None = None):
        if self.in_simulation:
            self.record_needed_resource(
                {"type": "named_container", "name": target_name})

        if target_name in self.fixture.names:
            target_pos = self.fixture.get_named_position(target_name)
            self.goto_pos(target_pos)
            self.current_container_name = target_name
            return

    def goto_well(self, wellid: str):
        if wellid is None and self.in_simulation:
            return
        if self.in_simulation:
            self.record_needed_resource(
                {"type": "well", "wellid": wellid})

        target_pos = Kinematic_State(self.fixture.get_named_position(wellid))
        self.current_container_name = wellid
        self.goto_pos(target_pos)

    def vto_steps(self, pumpid, vol):
        settings = self.settings()["machine"]["motors"]
        pump = settings["pumps"][pumpid]
        common = settings["common_settings"]
        rad_per_step = 2 * math.pi / common["pump_steps_per_revolution"]
        ul_per_step = pump["ul_per_rad"] * rad_per_step
        return round(pump["compensation_factor"] * vol / ul_per_step)

    def group_dispense(self, volumes: list[liq_handling_data]):
        self.move_complete.clear()
        move_data = []
        retract_move_data = []
        for liq_data in volumes:
            if liq_data.volume == 0:
                continue
            if liq_data.not_found and self.in_simulation:
                for pumpid_ind in range(self.pump_count):
                    if self.pump_map[pumpid_ind] == f"unknown_reagent_of_pump{pumpid_ind}":
                        liq_data.pumpid = pumpid_ind
                        self.set_pump_reagent(pumpid_ind, liq_data.reagent)
                        liq_data.not_found = False
                        break

            if liq_data.reagent is not None and self.in_simulation:
                self.record_needed_resource(
                    {"type": "reagent", "name": liq_data.reagent})
            if liq_data.pumpid is not None and self.in_simulation:
                self.record_needed_resource(
                    {"type": "pump", "id": liq_data.pumpid})

            if liq_data.not_found:
                if not self.in_simulation:
                    raise ValueError(f"missing reagent!: {liq_data}")
                continue

            # simulation / audit-trail handling
            if liq_data.volume > 0:
                target_line = self.pump_lines[liq_data.pumpid]
                end_of_line_reagent: Reagent_Mix = target_line[-1]
                released_volume = end_of_line_reagent.release_volume(
                    liq_data.volume)
                self.current_container.gain_mixed_volume(released_volume)
                if end_of_line_reagent.get_total_volume() == 0:
                    self.pump_lines.pop()
            else:
                self.pump_lines[liq_data.pumpid].append(
                    Reagent_Mix({"air_from_airgap_induced_by_negative_volume_dispense_call": liq_data.volume}))

            if not self.in_simulation:
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

        if not self.in_simulation:
            self.coms.queue_packet(packet.move_packet(move_data))
            self.coms.queue_packet(
                packet.make_int_vec_packet(codex.DELAY, [20]))
            self.coms.queue_packet(packet.move_packet(retract_move_data))
            self.coms.queue_packet(
                packet.make_int_vec_packet(codex.DELAY, [100]))

    def dispense(self, volume, reagent=None, pumpid=None):
        singlet_disp_data = liq_handling_data(
            self.pump_map, volume, pumpid=pumpid, reagent=reagent)
        self.group_dispense([singlet_disp_data])

    def aspirate(self, volume, pumpid):
        self.move_complete.clear()
        if pumpid is not None and self.in_simulation:
            self.record_needed_resource(
                {"type": "pump", "id": pumpid})

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

    def swap_reagent(self, old_reagent, new_reagent):
        # TODO THIS HAS TO MUTATE THE PUMPLINES GLOBAL!!
        pumpid = get_pump_id(old_reagent)
        pumpUpdate(id=pumpid, reagent=new_reagent)
