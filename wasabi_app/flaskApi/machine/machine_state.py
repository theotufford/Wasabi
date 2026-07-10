import time
from ..db import get_db
import math
import json
import RPi.GPIO as pio
from .kinematics import solve_5bar_FK, solve_5bar_IK, MachinePosition, Vec2d, make_pos
from .serialcoms import ComsChannel
from .utils import alph_to_vec


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
        self.position_known = False

        with open(settings_path, "r") as conf:
            self.settings = json.load(conf)

        self.motor_settings = self.settings["motors"]
        spr = "steps_per_rev"
        self.a_steps_per_rad = self.motor_settings["a"][spr] / (2 * math.pi)
        self.b_steps_per_rad = self.motor_settings["b"][spr] / (2 * math.pi)
        zsettings = self.motor_settings["z"]
        self.z_steps_per_mm = zsettings[spr] / zsettings["screw_pitch"]

        self.plate = Plate(self.settings["plates"]["standard 96"])
        self.coms.send_settings(self.settings)

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

    def dispense(self, reagent, volume):
        id = self.get_pump_id(reagent)
        if id is None:
            print(f"reagent '{reagent}' not found in pumpmap!")
            return False
        pump_settings = self.settings["motors"]["pumps"][id]
        rads_per_ul = 0.174532925  # guess at a constant, dependent on pump design
        # TODO ^ calibrate
        ul_per_rev = 1 / (rads_per_ul * 2 * math.pi)
        steps_per_ul = pump_settings["steps_per_rev"] / ul_per_rev
        total_steps = math.floor(
            pump_settings["compensation_factor"] * volume * steps_per_ul)
        self.coms.send_pump_action_steps(id, total_steps)

    def aspirate(self, reagent, volume):
        pass

    def to_csv(self):
        pass
