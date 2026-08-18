import time
import string
import copy
import asyncio
from ..db import get_db
import math
import inspect
import json
from typing import Self
import RPi.GPIO as pio
from .kinematics import solve_5bar_FK, solve_5bar_IK, MachinePosition, Vec2d, make_pos
from . import serialcoms as serlib
from .utils import alph_to_vec


class Reagent_Mix:
    def __init__(self):
        self.contents = {}

    def get_total_volume(self):
        total_volume = 0
        for reagent in self.contents:
            held_volume = self.contents[reagent]
            total_volume += held_volume
        return total_volume

    def release_volume(self, target_volume):
        total_volume = self.get_total_volume()
        if total_volume == 0:
            raise ValueError(
                f"attempting to release volume from empty reagent mix")

        released_volume = Reagent_Mix()

        if total_volume < target_volume:
            released_volume.contents = self.contents
            return released_volume

        v_total = self.get_total_volume()
        for reagent in self.contents:
            volume = (self.contents[reagent] / v_total) * target_volume
            self.contents[reagent] -= volume
            released_volume.contents[reagent] = volume

        return released_volume

    def __repr__(self):
        return f"{self.contents}"

    def gain_reagent(self, volume, reagent):
        if not self.contents.get(reagent):
            self.contents[reagent] = 0
        self.contents[reagent] += volume
        self.empty = False

    def gain_mixed_volume(self, liquid: Self):
        for reagent in liquid.contents:
            volume = liquid.contents[reagent]
            self.gain_reagent(volume, reagent)


class Well():
    def __init__(self, relative_position: Vec2d):
        self.relative_position = relative_position
        self.liquid = Reagent_Mix()

    def release_aspirate(self, volume) -> Reagent_Mix:
        return self.liquid.release_volume(volume)

    def gain_liquid(self, liquid: Reagent_Mix):
        return self.liquid.gain_mixed_volume(liquid)


class Plate:
    def __init__(self, settings: dict):
        self.rows = settings["rows"]
        self.columns = settings["columns"]
        self.spacing = settings["spacing"]
        self.by_alph: dict[str, Well] = self.make_clear_plate()

    def make_clear_plate(self):
        by_alph = {}
        for row_y in range(0, self.rows):
            alph = string.ascii_uppercase[row_y]
            for col_x in range(0, self.columns):
                by_alph[f"{alph}{
                    col_x + 1}"] = Well(self.spacing * Vec2d(col_x, row_y))
        return by_alph

    def reset_plate(self):
        self.by_alph = self.make_clear_plate()

    def get_well_vol_dict(self):
        out = {}
        for alph in self.by_alph:
            well = self.by_alph[alph]
            out[alph] = well.liquid.contents
        return out

    def __repr__(self):
        return f"{self.rows}x{self.columns}; {self.spacing}mm"


class Machine:
    def __init__(self, settings_path, method_library):
        self.current_position = MachinePosition()
        self.current_well = None
        self.home_offset = MachinePosition()
        self.methods: MethodLibrary = method_library
        self.methods.machine = self
        self.motors_enabled = True
        self.abs_plate_map = {}
        self.error = None
        self.position_known = False
        self.settings_path = settings_path
        self.run_is_simulation = False
        self.coms: serlib.ComsChannel

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
            line_contents.gain_reagent(999999999999999, "whatever is in this pump")
            self.pump_line_contents[id] = [line_contents]

        self.plate = Plate(self.settings()["plates"]["standard 96"])
        self.hw_init()

    def settings(self):
        with open(self.settings_path, "r") as conf:
            settings = json.load(conf)
            return settings

    def hw_init(self):
        # reboot the pico
        pi3b_pins = self.settings()["machine"]["pins"]["on_3b_server_board"]
        pico_reset_pin = pi3b_pins["pico_reset_pin"]
        stage_enable_pin = pi3b_pins["stage_enable_pin"]
        pump_ms1 = pi3b_pins["pump_ms1"]
        pump_ms2 = pi3b_pins["pump_ms2"]
        pio.setup(pico_reset_pin, pio.OUT)
        pio.setup(stage_enable_pin, pio.OUT)
        pio.setup(pump_ms1, pio.OUT)
        pio.setup(pump_ms2, pio.OUT)

        pio.output(stage_enable_pin, pio.HIGH)

        pio.output(pico_reset_pin, pio.LOW)
        time.sleep(0.1)
        pio.output(pico_reset_pin, pio.HIGH)
        time.sleep(0.1)
        coms = self.coms = serlib.ComsChannel()
        # send kinematic motor settings ------------
        motors = self.settings()["machine"]["motors"]
        common_settings = motors["common_settings"]
        a_mot_settings = [
            motors["a"]["stp_pin"],
            motors["a"]["dir_pin"],
            motors["a"]["invert_dir"],
            1600,  # hard coded to max microsteps
            common_settings["arms_angular_max_velocity"],
            common_settings["arms_angular_accel"]
        ]
        b_mot_settings = [
            motors["b"]["stp_pin"],
            motors["b"]["dir_pin"],
            motors["b"]["invert_dir"],
            1600,  # hard coded to max microsteps
            common_settings["arms_angular_max_velocity"],
            common_settings["arms_angular_accel"]
        ]
        z_mot_settings = [
            motors["z"]["stp_pin"],
            motors["z"]["dir_pin"],
            motors["z"]["invert_dir"],
            1600,  # hard coded to max microsteps
            common_settings["z_max_angular_velocity"],
            common_settings["z_angular_accel"]
        ]
        coms.send_int_vec(serlib.A_MOTOR, a_mot_settings)
        coms.get_confirm()
        coms.send_int_vec(serlib.B_MOTOR, b_mot_settings)
        coms.get_confirm()
        coms.send_int_vec(serlib.Z_MOTOR, z_mot_settings)
        coms.get_confirm()
        pump_microsteps = common_settings["pump_steps_per_revoulution"]
        # send pump motor settings -----------------
        for pump_conf in motors["pumps"]:
            pump_settings = [
                pump_conf["stp_pin"],
                pump_conf["dir_pin"],
                pump_conf["invert_dir"],
                pump_microsteps,
                pump_conf["ang_v_max"],
                pump_conf["ang_accel_rad"]
            ]
            coms.send_int_vec(serlib.NEW_PUMP, pump_settings)
            coms.get_confirm()

        # send other pico pin settings -------------
        pinsettings = self.settings()["machine"]["pins"]
        pins = [
            pinsettings["motor_enable_pin"],
            pinsettings["pump_enable_pin"],
            pinsettings["a_endstop"],
            pinsettings["b_endstop"],
            pinsettings["z_endstop"]
        ]

        coms.send_int_vec(serlib.MACHINE_PIN_DEFINITIONS, pins)
        coms.send_code(serlib.CONFIRM)
        coms.get_confirm()

        if pump_microsteps == 200:
            pio.output(pump_ms1, pio.LOW)
            pio.output(pump_ms2, pio.LOW)
        elif pump_microsteps == 400:
            pio.output(pump_ms1, pio.HIGH)
            pio.output(pump_ms2, pio.LOW)
        elif pump_microsteps == 800:
            pio.output(pump_ms1, pio.LOW)
            pio.output(pump_ms2, pio.HIGH)
        elif pump_microsteps == 1600:
            pio.output(pump_ms1, pio.HIGH)
            pio.output(pump_ms2, pio.HIGH)
        else:
            raise ValueError(f"pump microsteps malconfigured!!\
                             options are 200, 400, 800, 1600, currently\
                             configured to {pump_microsteps}")

        self.position_known = False
        self.current_position = MachinePosition()
        self.home_offset = MachinePosition()

    def coms_loop(self):
        while True:
            # probably do other stuff here also like alert
            asyncio.run(self.coms.get_packet())
            code = self.coms.most_recent_rx.code
            if code == serlib.WAKE:
                self.hw_init()

    def get_pos_FK(self, target: MachinePosition) -> MachinePosition:
        xy = solve_5bar_FK(self.settings(), target.alpha, target.beta)
        target.x = xy["x"]
        target.y = xy["y"]
        target.fksolved = True
        return target

    def get_pos_IK(self, pos_target: MachinePosition) -> MachinePosition:
        angles = solve_5bar_IK(self.settings(), pos_target.x, pos_target.y)
        pos_target.alpha = angles["alpha"]
        pos_target.beta = angles["beta"]
        pos_target.iksolved = True
        return pos_target

    def to_steps(self, pos: MachinePosition) -> dict:
        steps = {}
        steps["alpha"] = math.ceil(pos.alpha * self.a_steps_per_rad)
        steps["beta"] = math.ceil(pos.beta * self.b_steps_per_rad)
        steps["z"] = math.ceil(pos.z * self.z_steps_per_mm)
        return steps

    def from_steps(self, a, b, z) -> MachinePosition:
        given_pos = MachinePosition()
        given_pos.alpha = a / self.a_steps_per_rad
        given_pos.beta = b / self.b_steps_per_rad
        given_pos.z = z / self.z_steps_per_mm
        given_pos.iksolved = True
        given_pos = self.get_pos_FK(given_pos)
        return given_pos

    def goto_pos(self, pos: MachinePosition) -> None:
        if not self.position_known:
            print("trying to move absolutely without being homed!")
            return
        if not self.run_is_simulation:
            pos = self.get_pos_IK(pos)
            steps = self.to_steps(pos)
            self.coms.send_move_steps(**steps)
            self.current_position = pos
        self.current_well = None

    def goto_well(self, coord: str):
        pos = self.home_offset
        if self.current_well is not None:
            pos = pos + self.current_well.relative_position
        self.goto_pos(pos)
        self.current_well = self.plate.by_alph[coord]

    def get_reagent(self, id):
        db = get_db()
        reagent = db.execute("""
                          SELECT reagent FROM pumpMap
                          WHERE pumpID = ?
                          LIMIT 1
                          """, (id,)).fetchone()[0]
        return reagent

    def get_pump_id(self, reagent):
        # get pump map
        db = get_db()
        ID = db.execute("""
                          SELECT pumpID FROM pumpMap
                          WHERE reagent = ?
                          LIMIT 1
                          """, (reagent,)).fetchone()[0]
        return ID

    def send_pump_action(self, volume, id):
        motor_settings = self.settings()["machine"]["motors"]
        pump_settings = motor_settings["pumps"][id-1]

        ul_per_rad = pump_settings["ul_per_rad"]
        compensation_factor = pump_settings["compensation_factor"]
        spr = motor_settings["common_settings"]["pump_steps_per_revoulution"]

        speed = pump_settings["ang_v_max"]
        accel = pump_settings["ang_accel_rad"]

        droplet_retract_volume = pump_settings["droplet_vol_ul"]
        asp_speed = pump_settings["aspiration_ang_v"]

        ul_per_rev = ul_per_rad * 2 * math.pi * compensation_factor
        steps_per_ul = spr / ul_per_rev

        total_steps = math.floor(volume * steps_per_ul)
        retract_steps = math.floor(droplet_retract_volume * steps_per_ul)

        is_aspiration = volume < 0

        if not is_aspiration:
            self.coms.send_pump_action_steps(
                id, speed, accel, total_steps + retract_steps)
            self.coms.send_pump_action_steps(
                id, asp_speed, accel, -retract_steps)
        else:
            self.coms.send_pump_action_steps(id, asp_speed, accel, total_steps)

    def dispense(self, volume, reagent=None, id=None):
        if volume == 0:
            return
        if id is None:
            id = self.get_pump_id(reagent)
        held_volume = self.pump_line_contents[id][-1]
        output_liquid = held_volume.release_volume(volume)
        if held_volume.get_total_volume() == 0:
            self.pump_line_contents.pop()

        self.current_well.gain_liquid(output_liquid)

        if not self.run_is_simulation:
            self.send_pump_action(volume, id)

    def aspirate(self,  volume, id):
        if volume == 0:
            return
        pump_line = self.pump_line_contents[id]
        aspirated_liquid = self.current_well.release_volume(volume)
        pump_line.append(aspirated_liquid)
        if not self.run_is_simulation:
            self.send_pump_action(volume, id)


class MethodLibrary:
    def __init__(self):
        self.method_callables = {}
        self.method_info = {}
        self.machine: Machine

    def call_method(self, name, args_dict):
        inputs = self.method_info[name]["inputs"]
        valid_keys = [input["name"] for input in inputs]
        args_dict = {key: value for key,
                     value in args_dict.items() if key in valid_keys}
        self.method_callables[name](machine=self.machine, **args_dict)

    def simulate_experiment(self, data) -> Plate:
        pre_sim_machine = copy.deepcopy(self.machine)
        self.machine.run_is_simulation = True
        self.machine.position_known = True
        pump_id = 0
        seen_reagents = []
        for form_id in data["forms"]:
            form = data["forms"][form_id]
            reagent = form.get("reagent")
            if reagent not in seen_reagents:
                seen_reagents.append(reagent)
                reagent_line = self.machine.pump_line_contents[pump_id][0]
                reagent_line.gain_reagent(999999999999999, reagent)
                pump_id += 1
            name = form["method"]
            print(f"pump lines configured: {self.machine.pump_line_contents}")
            self.call_method(name, form)
        output_plate = copy.deepcopy(self.machine.plate)
        self.machine = pre_sim_machine
        return output_plate

    def run_experiment(self, data):
        for form_id in data["forms"]:
            form = data["forms"][form_id]
            name = form["method"]
            self.call_method(name, form)
        self.machine.goto_pos(self.machine.home_offset)
        return self.machine.plate

    def register_method(self, method_function, other=None):
        sig = inspect.signature(method_function)
        args = dict(sig.parameters.items())
        method_name = method_function.__name__
        if not args.get("machine") or not args["machine"].annotation == Machine:
            raise ValueError(f"method: {method_name} needs machine parameter!")
        self.method_callables[method_name] = method_function
        self.method_info[method_name] = {"inputs": [], "other": other}
        for arg_name in args:
            param = args[arg_name]
            annotation = param.annotation

            if annotation.__name__ == "Machine":
                continue
            sub_args: tuple | None = None
            try:
                sub_args = annotation.__args__
            except AttributeError:
                print(f"param {arg_name} doesnt have any sub-arguments")

            self.method_info[method_name]["inputs"].append({
                "name": arg_name,
                "type": annotation.__name__,
                "args": sub_args
            })

    def output_methods_outline(self):
        with open("private/methods.json", "w") as file:
            file.write(json.dumps(self.method_info))
