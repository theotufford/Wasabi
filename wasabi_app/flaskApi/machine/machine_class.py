from container_class import Plate, Reagent_Mix, Well
import copy
import json
import time
from typing import Literal
import asyncio
from ..db import get_db
import math
import inspect
import RPi.GPIO as pio
from .kinematics import solve_5bar_FK, solve_5bar_IK, Vec2d, Vec3d, Vec2d_Ang
from . import serialcoms as serlib


class Machine:
    pass


class Kinematic_State():
    def __init__(self, cartesian_position: Vec3d | None = None, angular_position: Vec2d_Ang | None = None):
        self.iksolved = angular_position is None
        self.fksolved = cartesian_position is None
        self.angular_position = angular_position
        self.position = cartesian_position
        if not self.fksolved:
            cartesian_position = Vec3d([0, 0, 0])

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
        self.machine.in_simulation = True
        self.machine.position_known = True
        pump_id = 0
        seen_reagents = []
        for form_id in data["forms"]:
            form = data["forms"][form_id]
            reagent = form.get("reagent")
            if reagent not in seen_reagents:
                seen_reagents.append(reagent)
                reagent_line = Reagent_Mix()
                reagent_line.gain_reagent(reagent, reservoir=True)
                self.machine.pump_line_contents[id] = [reagent_line]
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

    def register_method(self,
                        method_function,
                        # TODO purity inference
                        function_purity: Literal["impure", "pure"] = "pure"):

        sig = inspect.signature(method_function)
        args = dict(sig.parameters.items())
        method_name = method_function.__name__

        if not args.get("machine") or not args["machine"].annotation == Machine:
            raise ValueError(f"method: {method_name} needs machine parameter!")

        self.method_callables[method_name] = method_function
        is_direct_input = "volume_map" in args.keys()
        has_region_select = "well_array" in args.keys()
        has_region_select = has_region_select or "well_array_dict" in args.keys()

        info = {
            "inputs": [],
            "purity": function_purity,
            "has_region_select": has_region_select,
            "is_direct_input": is_direct_input
        }

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

            info["inputs"].append({
                "name": arg_name,
                "type": annotation.__name__,
                "args": sub_args
            })
            self.method_info[method_name] = info

    def output_methods_outline(self):
        with open("private/methods.json", "w") as file:
            file.write(json.dumps(self.method_info))


class Machine:
    def __init__(self, settings_path, method_library):
        self.settings_path = settings_path
        mach = self.settings()["machine"]
        self.current_position = Vec3d()
        self.home_offset = Vec3d()
        self.aspiration_depth_offset = 0
        self.methods: MethodLibrary = method_library
        self.methods.machine = self
        self.motors_enabled = True
        self.abs_plate_map = {}
        self.error = None
        self.position_known = False
        self.in_simulation = False
        self.impure_method_flag = False
        self.coms: serlib.ComsChannel
        self.waste_well = Well(
            self.settings()["plates"]["150ml_waste_beaker"], Vec2d(0, 0))
        self.current_well = self.waste_well
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

    def settings(self):
        with open(self.settings_path, "r") as conf:
            settings = json.load(conf)
            return settings

    def reboot_pico(self):
        pi3b_pins = self.settings()["machine"]["pins"]["on_3b_server_board"]
        pico_reset_pin = pi3b_pins["pico_reset_pin"]
        stage_enable_pin = pi3b_pins["stage_enable_pin"]
        pio.setup(pico_reset_pin, pio.OUT)
        pio.setup(stage_enable_pin, pio.OUT)

        pio.output(stage_enable_pin, pio.HIGH)

        pio.output(pico_reset_pin, pio.LOW)
        time.sleep(0.1)
        pio.output(pico_reset_pin, pio.HIGH)
        time.sleep(0.1)

        motors = self.settings()["machine"]["motors"]
        common_settings = motors["common_settings"]
        pump_microsteps = common_settings["pump_steps_per_revoulution"]
        pump_ms1 = pi3b_pins["pump_ms1"]
        pump_ms2 = pi3b_pins["pump_ms2"]
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

    def hw_init(self):
        self.reboot_pico()
        # TODO SEND SETTINGS VECTOR
        self.position_known = False
        self.current_position = Kinematic_State()
        self.home_offset = Kinematic_State()

    def coms_loop(self):
        while True:
            # probably do other stuff here also like alert
            asyncio.run(self.coms.get_packet())
            code = self.coms.most_recent_rx.code
            if code == serlib.WAKE:
                self.hw_init()

    def get_pos_FK(self, target: Kinematic_State) -> Kinematic_State:
        xy = solve_5bar_FK(self.settings(), target.alpha, target.beta)
        target.x = xy["x"]
        target.y = xy["y"]
        target.fksolved = True
        return target

    def get_pos_IK(self, pos_target: Kinematic_State) -> Kinematic_State:
        angles = solve_5bar_IK(self.settings(), pos_target.x, pos_target.y)
        pos_target.alpha = angles["alpha"]
        pos_target.beta = angles["beta"]
        pos_target.iksolved = True
        return pos_target

    def to_steps(self, pos: Kinematic_State) -> dict:
        steps = {}
        steps["alpha"] = math.ceil(pos.alpha * self.a_steps_per_rad)
        steps["beta"] = math.ceil(pos.beta * self.b_steps_per_rad)
        steps["z"] = math.ceil(pos.z * self.z_steps_per_mm)
        return steps

    def from_steps(self, a, b, z) -> Kinematic_State:
        given_pos = Kinematic_State()
        given_pos.alpha = a / self.a_steps_per_rad
        given_pos.beta = b / self.b_steps_per_rad
        given_pos.z = z / self.z_steps_per_mm
        given_pos.iksolved = True
        given_pos = self.get_pos_FK(given_pos)
        return given_pos

    def goto_pos(self, pos: Kinematic_State) -> None:
        if not self.position_known:
            return
        if not self.in_simulation:
            pos = self.get_pos_IK(pos)
            steps = self.to_steps(pos)
            self.coms.send_move_steps(**steps)
            self.current_position = pos
            self.current_well = self.plate.by_position(
                self.current_position)

    def stall_for_confirm(self, confirm_prompt_message):
        if not self.in_simulation:
            input(f"{confirm_prompt_message}")

    def goto_well(self, wellid: str):
        if wellid == "waste":
            target_pos = self.waste_well.absolute_position
            if target_pos is None:
                raise ValueError("position of waste well is unknown!")
            self.goto_pos(target_pos)
            self.current_well = self.waste_well
            return

        target_well = self.plate.by_alph(wellid)
        target_pos = target_well.absolute_position
        print(f"going to well at target position: {target_pos}")
        self.goto_pos(target_pos)

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
        pump_settings = motor_settings["pumps"][id]

        ul_per_rad = pump_settings["ul_per_rad"]
        compensation_factor = pump_settings["compensation_factor"]
        spr = motor_settings["common_settings"]["pump_steps_per_revoulution"]

        speed = pump_settings["ang_v_max"]
        accel = pump_settings["ang_accel_rad"]

        droplet_retract_volume = pump_settings["droplet_vol_ul"]
        overshoot_volume = pump_settings["overshoot_offset_ul"]
        asp_speed = pump_settings["aspiration_ang_v"]

        ul_per_rev = ul_per_rad * 2 * math.pi / compensation_factor
        steps_per_ul = spr / ul_per_rev

        total_steps = math.floor(volume * steps_per_ul)

        is_aspiration = volume < 0

        if not is_aspiration:
            retract_steps = math.floor(droplet_retract_volume * steps_per_ul)
            overshoot_steps = math.floor(overshoot_volume * steps_per_ul)
            self.coms.send_pump_action_steps(
                id, speed, accel, total_steps + retract_steps + overshoot_steps)
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

        if not self.in_simulation:
            self.send_pump_action(volume, id)

    def aspirate(self, volume, id):
        self.impure_method_flag = True
        if volume == 0:
            return
        if volume > 0:
            raise ValueError("trying to aspirate positive volume?")
        pump_line = self.pump_line_contents[id]
        reagent_contents = Reagent_Mix()
        if self.current_position.z <= self.home_offset.z:
            reagent_contents = Reagent_Mix(contents={"air": abs(volume)})
            pump_line.append(reagent_contents)

        if not self.in_simulation:
            self.send_pump_action(-volume, id)
