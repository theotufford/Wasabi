import time
import asyncio
from ..db import get_db
import math
import inspect
import json
import RPi.GPIO as pio
from .kinematics import solve_5bar_FK, solve_5bar_IK, MachinePosition, Vec2d, make_pos
from . import serialcoms as serlib
from .utils import alph_to_vec


class Plate:
    def __init__(self, settings: dict):
        self.rows = settings["rows"]
        self.columns = settings["columns"]
        self.spacing = settings["spacing"]

    def __repr__(self):
        return f"{self.rows}x{self.columns}; {self.spacing}mm"


class Machine:
    def __init__(self, settings_path):
        self.current_position = MachinePosition()
        self.home_offset = MachinePosition()
        self.motors_enabled = True
        self.abs_plate_map = {}
        self.error = None
        self.position_known = False

        self.coms: serlib.ComsChannel

        with open(settings_path, "r") as conf:
            self.settings = json.load(conf)

        mach = self.settings["machine"]
        spr = mach["motors"]["common_settings"]["kinematic_steps_per_revolution"]
        pitch = mach["machineDimensions"]["z_screw_pitch"]
        self.a_steps_per_rad = spr / (2 * math.pi)
        self.b_steps_per_rad = spr / (2 * math.pi)
        self.z_steps_per_mm = spr / pitch

        self.plate = Plate(self.settings["plates"]["standard 96"])
        self.hw_init()

    def hw_init(self):
        # reboot the pico
        pi3b_pins = self.settings["machine"]["pins"]["on_3b_server_board"]
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
        motors = self.settings["machine"]["motors"]
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
            common_settings["arms_angular_max_velocity"],
            common_settings["arms_angular_accel"]
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
        pinsettings = self.settings["machine"]["pins"]
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
            raise ValueError(f"pump microsteps malconfigured!! options are 200, 400, 800, 1600, currently configured to {
                             pump_microsteps}")

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
        xy = solve_5bar_FK(self.settings, target.alpha, target.beta)
        target.x = xy["x"]
        target.y = xy["y"]
        target.fksolved = True
        return target

    def get_pos_IK(self, pos_target: MachinePosition) -> MachinePosition:
        angles = solve_5bar_IK(self.settings, pos_target.x, pos_target.y)
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
        pos = self.get_pos_IK(pos)
        steps = self.to_steps(pos)
        self.coms.send_move_steps(**steps)
        self.current_position = pos

    def populate_plate_map(self) -> None:
        relative = {}
        for alph_row_ind in range(0, self.plate.rows):
            alph = chr(alph_row_ind + 65)
            for col_id in range(0, self.plate.columns):
                col_x = - col_id * self.plate.spacing
                row_y = alph_row_ind * self.plate.spacing
                relative[f"{alph}{col_id + 1}"] = Vec2d(col_x, row_y)
        print(f"relative: {relative}")
        for wellID in relative:
            well_rel_vec = relative[wellID]
            endpt = self.home_offset + well_rel_vec
            print(f"endpt: {endpt}")
            self.abs_plate_map[wellID] = self.get_pos_IK(endpt)

    def goto_well(self, coord: str):
        well_position_vector = alph_to_vec(coord) * self.plate.spacing
        pos = self.home_offset + well_position_vector
        print(f"""got goto_well: {coord})
        set to go to: {pos.x} {pos.y}
        home offset is: {self.home_offset}
        well_position_vector is: {well_position_vector.x, well_position_vector.y}
        """)

        self.goto_pos(pos)

    def get_pump_id(self, reagent):
        # get pump map
        db = get_db()
        ID = db.execute("""
                          SELECT pumpID FROM pumpMap
                          WHERE reagent = ?
                          LIMIT 1
                          """, (reagent,)).fetchone()[0]
        return ID

    def send_pump_action(self, volume, reagent=None, id=None):
        if reagent is not None:
            id = self.get_pump_id(reagent)
            if id is None:
                print(f"reagent '{reagent}' not found in pumpmap!")
                return False
        if reagent is None and id is None:
            raise ValueError()

        motor_settings = self.settings["machine"]["motors"]
        pump_settings = motor_settings["pumps"][id-1]

        speed = pump_settings["ang_v_max"]
        accel = pump_settings["ang_accel_rad"]

        ul_per_rad = pump_settings["ul_per_rad"]
        compensation_factor = pump_settings["compensation_factor"]
        spr = motor_settings["common_settings"]["pump_steps_per_revoulution"]

        ul_per_rev = ul_per_rad * 2 * math.pi * compensation_factor
        steps_per_ul = spr / ul_per_rev
        total_steps = math.floor(volume * steps_per_ul)
        self.coms.send_pump_action_steps(id, speed, accel, total_steps)

    def dispense(self, volume, reagent=None, id=None):
        self.send_pump_action(volume, reagent, id)

    def aspirate(self, reagent, volume):
        self.send_pump_action(-volume, reagent, id)


class MethodLibrary:
    def __init__(self, machine: Machine):
        self.method_callables = {}
        self.method_info = {}
        self.machine = machine

    def call_method(self, name, args_dict):

    def register_method(self, method_function, other=None):
        sig = inspect.signature(method_function)
        args = dict(sig.parameters.items())
        method_name = method_function.__name__
        if not args.get("machine") or not args["machine"].annotation == Machine:
            raise ValueError(f"method: {method_name} needs machine parameter!")
        self.method_callables[method_name] = method_function
        self.method_info[method_name] = {"inputs":[], "other": other}
        for arg_name in args:
            param = args[arg_name]
            if param.annotation.__name__ == Machine:
                continue
            self.method_info[method_name]["inputs"].append({
                    "name": arg_name,
                    "type": param.annotation.__name__
                })

    def update_(self):

