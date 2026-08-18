from flask import Flask, jsonify, Blueprint, request, session
from typing import Literal
from .machine.machine_state import Machine, MethodLibrary
from .machine.kinematics import Vec2d, dot_product
from .machine.utils import alph_to_vec, get_linear_well_array_height, get_linear_well_array_width, xy_to_alph

methods = MethodLibrary()


@methods.register_method
def volume_map(machine: Machine,
               volume_array: list,
               reagent):
    for row_id in volume_array:
        row = volume_array[row_id]
        for col_id in range(0, len(row)):
            volume_target = row[col_id]
            if volume_target == 0:
                continue
            wellid = xy_to_alph(col_id, row_id)
            machine.goto_well(wellid)


@methods.register_method
def constant(machine: Machine,
             well_array,
             reagent,
             volume: float):
    for well in well_array:
        machine.goto_well(well)
        machine.dispense(volume, reagent=reagent)


def general_gradient(machine: Machine,
                     well_array,
                     reagent,
                     direction: Literal["up", "down", "left", "right"],
                     gradient_type: Literal["spacing", "end target"],
                     spacing_type: Literal["linear", "exponential"],
                     initial_volume: float = 0,
                     final_volume: float = 0,
                     spacing_coefficient: float = 1,
                     ):
    # the reason y is flipped is because we are
    # translating row n as being n units in the +y direction
    well_plate_basis = {
        "right": Vec2d(1, 0),
        "down": Vec2d(0, 1),
        "up": Vec2d(0, -1),
        "left": Vec2d(-1, 0)
    }

    if direction in ["left", "up"]:
        well_array = well_array.reverse()

    initial_pos = alph_to_vec(well_array[0])

    # fixes bad input by rotating
    # WPB vector 180 degrees because its assumed a negative spacing coefficient
    # is meant to indicate decrement
    spacing_coefficient_sign = spacing_coefficient / abs(spacing_coefficient)

    spacing_vec = well_plate_basis[direction] * spacing_coefficient_sign

    if gradient_type == "end target":
        step_count = 1
        if direction == "right":
            step_count = get_linear_well_array_width(well_array)
        if direction == "down":
            step_count = get_linear_well_array_height(well_array)

        delta_v = final_volume - initial_volume
        delta_v_sign = delta_v / abs(delta_v)

        spacing_vec *= delta_v_sign

        spacing_coefficient = 1
        if spacing_type == "linear":
            spacing_coefficient = abs(delta_v) / step_count
        if spacing_type == "exponential":
            spacing_coefficient = (
                final_volume/initial_volume) ** (1/step_count)

    for well in well_array:
        relative_postion = alph_to_vec(well) - initial_pos

        volume: float

        print(f"spacing vec {spacing_vec}")
        print(f" coefficient {spacing_coefficient}")

        if spacing_type == "linear":
            volume = initial_volume + \
                dot_product(relative_postion, spacing_vec)
        if spacing_type == "exponential":
            volume = initial_volume * \
                (spacing_coefficient ** dot_product(relative_postion, spacing_vec))

        machine.goto_well(well)
        machine.dispense(volume, reagent)


@methods.register_method
def incremental_gradient(machine: Machine,
                         well_array,
                         reagent,
                         direction: Literal["up", "down", "left", "right"],
                         increment: float,
                         initial_volume: float):
    general_gradient(machine, well_array, reagent, direction,
                     gradient_type="spacing",
                     spacing_type="linear",
                     initial_volume=initial_volume,
                     spacing_coefficient=increment)


@methods.register_method
def exponential_gradient(machine: Machine,
                         well_array,
                         reagent,
                         direction: Literal["up", "down", "left", "right"],
                         base: float,
                         initial_volume: float):

    general_gradient(machine, well_array, reagent, direction,
                     gradient_type="spacing",
                     spacing_type="exponential",
                     initial_volume=initial_volume,
                     spacing_coefficient=base)


@methods.register_method
def end_target_gradient(machine: Machine,
                        well_array,
                        reagent,
                        direction: Literal["down", "right"],
                        spacing_type: Literal["linear", "exponential"],
                        top_left_volume: float,
                        bottom_right_volume: float):

    general_gradient(machine, well_array, reagent, direction,
                     gradient_type="end target",
                     spacing_type=spacing_type,
                     initial_volume=top_left_volume,
                     final_volume=bottom_right_volume
                     )
