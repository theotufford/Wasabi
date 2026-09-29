from container_class import Plate, Reagent_Mix, Well
from method_library import MethodLibrary
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
    def __init__(self, cartesian_position: Vec2d | Vec3d = Vec3d([0, 0, 0]), angular_position: Vec2d_Ang | None = None):
        self.iksolved = angular_position is None
        self.fksolved = cartesian_position.x != 0 or cartesian_position.y != 0
        self.angular_position = angular_position
        self.position = cartesian_position
        if type(cartesian_position) is Vec2d:
            cartesian_position = Vec3d([*cartesian_position.elements, 0])

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
        mach = self.settings()["machine"]
        self.current_position = Vec3d()
        self.home_offset = Vec3d()
        self.aspiration_depth_offset = 0
        self.methods: MethodLibrary = method_library
        self.methods.machine = self
        self.error = None
        self.position_known = False
        self.in_simulation = False
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

    def get_pos_FK(self, target: Kinematic_State) -> Kinematic_State:
        solved = solve_5bar_FK(self.settings(),
                               target.angular_position)
        output_position = Vec3d([*solved.elements, target.position.z])
        output = Kinematic_State(output_position, target.angular_position)
        return output

    def get_pos_IK(self, target: Kinematic_State) -> Kinematic_State:
        angular_target = solve_5bar_IK(
            self.settings(), target.position)
        output = Kinematic_State(target.position, angular_target)
        return output

    def to_steps(self, pos: Kinematic_State) -> dict:
        steps = {}
        steps["alpha"] = math.ceil(pos.alpha * self.a_steps_per_rad)
        steps["beta"] = math.ceil(pos.beta * self.b_steps_per_rad)
        steps["z"] = math.ceil(pos.z * self.z_steps_per_mm)
        return steps

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
