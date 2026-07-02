# this file creates an abstract interface for our code to easily program
# the robot to do certain methods  without the granularity of programming
# each and every action

from db import get_db
from serialcoms import Packet, abs_move_packet, rel_move_packet
from machine_state import Machine

# this function maps a1 -> [0,0]


def corners_to_range(from_input: str, to_input: str):
    fromchar = from_input[0]
    tochar = to_input[0]
    from_x = (ord(fromchar) - ord('A'))
    to_x = (ord(tochar) - ord('A'))
    from_y = int(from_input[1] - 1)
    to_y = int(to_input[1] - 1)

    if from_x > to_x:
        from_x, to_x = to_x, from_x

    if from_y > to_y:
        from_y, to_y = to_y, from_y

    all_wells = []

    for x in range(from_x, to_x):
        for y in range(from_y, to_y):
            all_wells.append([x, y])

    return all_wells


def run_experiment(machine: Machine, data):
    forms = data["forms"]

    for instruction_form in forms:
        method = instruction_form["method"]
        if method == "constant":
            constant_volume(instruction_form)
        if method == "gradient":
            gradient_volume(instruction_form)
        if method == "serial_dilution":
            serial_dilution(instruction_form)


def constant_volume(input_data: dict, machine: Machine):
    well_array = corners_to_range(input_data["from"], input_data["to"])

    for well in well_array:
        machine.move_to_well(well)
        machine.dispense(input_data["reagent"], input_data["volume"])


def gradient_volume(input_data: dict, machine: Machine):
    well_array = corners_to_range(input_data["from"], input_data["to"])
    direction = input_data["direction"]
    current_volume = input_data["initial_volume"]
    if direction == "up":
    # initialize this variable
    for well in well_array:
        machine.move_to_well(well)
        machine.dispense(input_data["reagent"], input_data["volume"])


def serial_dilution(input_data: dict, machine: Machine):
    pass
