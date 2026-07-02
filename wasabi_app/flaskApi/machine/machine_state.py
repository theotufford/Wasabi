import time
from db import get_db
import math
import json
import RPi.GPIO as pio
from kinematics import solve_5bar_FK, solve_5bar_IK, MachinePosition, Vec2d
from serialcoms import ComsChannel


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

        with open(settings_path, "r") as conf:
            self.settings = json.load(conf)

        self.motor_settings = self.settings["motors"]
        spr = "steps_per_rev"
        self.a_steps_per_rad = self.motor_settings["a"][spr] / 2 * math.pi
        self.b_steps_per_rad = self.motor_settings["b"][spr] / 2 * math.pi
        zsettings = self.motor_settings["z"]
        self.z_steps_per_mm = zsettings[spr] / zsettings["screw_pitch"]

        self.plate = Plate(self.settings["plates"]["standard 96"])
        self.abs_plate_map: dict | None = None

    def generate_plate_map(self):
        position_to_solve = self.home_offset.toolhead
        for alph_ind in range(0, self.plate.rows):
            alph = chr(alph_ind + 65)
            for num in range(0, self.plate.columns):
                key = f"{alph}{num}"
                self.abs_plate_map[key] = solve_5bar_IK(position_to_solve)
                position_to_solve.x -= self.plate.spacing
            position_to_solve.y += self.plate.spacing

    def set_plate(self, name: str):
        self.plate = Plate(self.settings["plates"][name])

    def move_to_well(self, coord: str):
        pos: MachinePosition | None = self.abs_plate_map.get(coord)
        if pos is None:
            raise ValueError(f"""probably the wrong plate is selected!
                             looking for well {coord}
                             on plate: {self.plate}
                             """)

        alpha_step_pos_abs = self.a_steps_per_rad * pos.alpha
        beta_step_pos_abs = self.b_steps_per_rad * pos.beta

        self.coms.send_move_steps(alpha_step_pos_abs, beta_step_pos_abs, 0)

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

    def aspirate(self, reagent, volume):
        pass

    def to_csv(self):
        pass
