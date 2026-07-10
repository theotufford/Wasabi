# this file creates an abstract interface for our code to easily program
# the robot to do certain methods  without the granularity of programming
# each and every action

from ..db import get_db
from .machine_state import Machine
from .kinematics import Vec2d, dot_product
from .utils import alph_to_vec, order_from_to_alphs, corners_to_range
import json


def run_experiment(machine: Machine, data):
    def constant_volume(instruction_form: dict):
        print("constant volume to run")
        print("data: ", instruction_form)
        well_array = corners_to_range(
            instruction_form["from"], instruction_form["to"])
        print(f"well array for this form: {well_array}")
        for well in well_array:
            machine.goto_well(well)
            vol_ul = float(instruction_form["methodObject"]["constantVolume"])
            machine.dispense(
                instruction_form["reagent"], vol_ul)

    def gradient_volume(instruction_form: dict):
        from_input, to_input = order_from_to_alphs(
            instruction_form["from"], instruction_form["to"])

        well_array = corners_to_range(from_input, to_input)
        direction = instruction_form["direction"]
        increment = instruction_form["increment"]
        initial_volume = instruction_form["initial_volume"]
        basis_def = {
            "up": Vec2d(0, -1),
            "down": Vec2d(0, 1),
            "left": Vec2d(-1, 0),
            "right": Vec2d(1, 0)
        }

        delta_vec = basis_def[direction] * increment

        if direction in ["left", "up"]:
            well_array = well_array.reverse()

        initial_pos = alph_to_vec(well_array[0])

        for well in well_array:
            relative_postion = alph_to_vec(well) - initial_pos
            volume = initial_volume + dot_product(relative_postion, delta_vec)

            machine.goto_well(well)
            machine.dispense(instruction_form["reagent"],  volume)

    def serial_dilution(instruction_form: dict):
        pass

    forms = (data["forms"]).items()
    for id, instruction_form in forms:
        print(f"body: {instruction_form}")
        method = instruction_form["method"]
        if method == "constant":
            constant_volume(instruction_form)
        if method == "gradient":
            gradient_volume(instruction_form)
        if method == "serial_dilution":
            serial_dilution(instruction_form)

    machine.goto_pos(machine.home_offset)
