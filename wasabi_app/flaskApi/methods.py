from flask import Flask, jsonify, Blueprint, request, session
from typing import Literal
from .machine.machine_state import Machine, MethodLibrary
from .machine.kinematics import Vec2d, dot_product
from .machine.utils import alph_to_vec, get_linear_well_array_height, get_linear_well_array_width

methods = MethodLibrary()


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
                     spacing_coeficcient: float = 1,
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
    # WPB vector 180 degrees because its assumed a negative spacing coeficcient
    # is meant to indicate decrement
    spacing_coeficcient_sign = spacing_coeficcient / abs(spacing_coeficcient)

    spacing_vec = well_plate_basis[direction] * spacing_coeficcient_sign

    if gradient_type == "end target":
        sizeval = 1
        if direction is "right":
            sizeval = get_linear_well_array_width(well_array)
        if direction is "down":
            sizeval = get_linear_well_array_height(well_array)

        delta_v = final_volume - initial_volume
        delta_v_sign = delta_v / abs(delta_v)

        spacing_vec *= delta_v_sign

        if spacing_type is "linear":
            spacing_coeficcient = abs(delta_v) / sizeval
            spacing_vec *= spacing_coeficcient
        if spacing_type is "exponential":
            spacing_coeficcient = abs(delta_v) ** (1/sizeval)

    for well in well_array:
        relative_postion = alph_to_vec(well) - initial_pos

        volume: float

        if spacing_type is "linear":
            volume = initial_volume + \
                dot_product(relative_postion, spacing_vec)
        if spacing_type is "exponential":
            volume = initial_volume + \
                spacing_coeficcient ** dot_product(
                    relative_postion, spacing_vec)

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
                     spacing_coeficcient=increment)


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
                     spacing_coeficcient=base)


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
                     initial_volume=top_left_volume)
