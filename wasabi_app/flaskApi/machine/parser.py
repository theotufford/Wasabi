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
            machine.dispense(vol_ul, reagent=instruction_form["reagent"])

    def gradient_volume(instruction_form: dict):
        from_input, to_input = order_from_to_alphs(
            instruction_form["from"], instruction_form["to"])

        well_array = corners_to_range(from_input, to_input)

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
