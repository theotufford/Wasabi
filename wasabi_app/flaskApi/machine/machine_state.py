import time
from ..db import get_db
import math
import json
import RPi.GPIO as pio
from .kinematics import solve_5bar_FK, solve_5bar_IK, MachinePosition, Vec2d
from .serialcoms import ComsChannel


class Plate:
    def __init__(self, settings: dict):
        self.rows = settings["rows"]
        self.columns = settings["columns"]
        self.spacing = settings["spacing"]

    def __repr__(self):
        return f"{self.rows}x{self.columns}; {self.spacing}mm"


class Machine:
    def __init__(self, coms: ComsChannel, settings_path):
        self.current_position = MachinePosition()
        self.home_offset = MachinePosition()
        self.motors_enabled = True
        self.coms = coms
        self.abs_plate_map = {}
        self.error = None

        with open(settings_path, "r") as conf:
            self.settings = json.load(conf)

        self.motor_settings = self.settings["motors"]
        spr = "steps_per_rev"
        self.a_steps_per_rad = self.motor_settings["a"][spr] / 2 * math.pi
        self.b_steps_per_rad = self.motor_settings["b"][spr] / 2 * math.pi
        zsettings = self.motor_settings["z"]
        self.z_steps_per_mm = zsettings[spr] / zsettings["screw_pitch"]

        self.plate = Plate(self.settings["plates"]["standard 96"])
        self.coms.send_settings(self.settings)

    def solve_5bar_FK(self, alpha: float, beta: float) -> Vec2d:
        try:
            val = solve_5bar_FK(self.settings, alpha, beta)
        except ValueError:
            self.error = "out of range!!"
            return None
        return val

    def solve_5bar_IK(self, target: Vec2d) -> MachinePosition:
        try:
            val = solve_5bar_IK(self.settings, target)
        except ValueError:
            self.error = "out of range!!"
            return None
        return val

    def generate_plate_map(self):
        relative = {}
        for alph_ind in range(0, self.plate.rows + 1):
            alph = chr(alph_ind + 65)
            for col_id in range(0, self.plate.columns):
                relative[f"{alph}{col_id + 1}"] = [-col_id *
                                                   self.plate.spacing, alph_ind * self.plate.spacing]
        print(relative)
        for rel in relative.values():
            relative_pos = Vec2d(rel[0], rel[1])
            abs_pos = relative_pos + \
                Vec2d(self.home_offset.x, self.home_offset.y)
            print(f"solving for {abs_pos}")
            angles = self.solve_5bar_IK(abs_pos)
            alpha = math.ceil(angles.alpha * self.a_steps_per_rad)
            beta = math.ceil(angles.beta * self. b_steps_per_rad)
            rel = [alpha, beta]

        self.abs_plate_map = rel

    def set_plate(self, name: str):
        self.plate = Plate(self.settings["plates"].get(name))
        self.abs_plate_map = {}
        self.generate_plate_map()

    def move_to_well(self, coord: str):
        pos = self.abs_plate_map.get(coord)
        if pos is None:
            raise ValueError(f"""probably the wrong plate is selected!
                             looking for well {coord}
                             on plate: {self.plate}
                             """)

        alpha_target = math.ceil(self.a_steps_per_rad * pos.alpha)
        beta_target = math.ceil(self.b_steps_per_rad * pos.beta)
        z_target = math.ceil(self.current_position.z * self.z_steps_per_mm)

        self.coms.send_move_steps(alpha_target, beta_target, z_target)

    def get_pump_id(self, reagent):
        # get pump map
        db = get_db()
        ID = db.execute("""
                          SELECT pumpID FROM pumpMap
                          WHERE reagent = ?
                          LIMIT 1
                          """, (reagent)).fetchone()
        return ID

    def dispense(self, reagent, volume):
        id = self.get_pump_id(reagent)
        if id is None:
            print(f"reagent '{reagent}' not found in pumpmap!")
            return False
        pump_settings = self.settings["pumps"][ID]
        self.coms.send_pump_action_steps(id, )

    def aspirate(self, reagent, volume):
        pass

    def to_csv(self):
        pass
