from flask import Flask, jsonify, Blueprint, request, session
import asyncio
from .db import get_db
import threading
import time
import json
from .machine.machine_state import Machine, MethodLibrary
from .kinematics import Vec2d, dot_product
from .utils import alph_to_vec, order_from_to_alphs, corners_to_range


methods = MethodLibrary()


@methods.register_method
def constant(machine: Machine,
             well_array,
             volume,
             reagent):
    for well in well_array:
        machine.goto_well(well)
        machine.dispense()


@methods.register_method
def incremental_gradient(machine: Machine,
                         well_array,
                         reagent,
                         direction,
                         increment,
                         initial_volume):
    std_basis = {
            "up": Vec2d(0, -1),
            "down": Vec2d(0, 1),
            "left": Vec2d(-1, 0),
            "right": Vec2d(1, 0)
            }

   delta_vec = std_basis[direction] * increment

   if direction in ["left", "up"]:
       well_array = well_array.reverse()

    initial_pos = alph_to_vec(well_array[0])

    for well in well_array:
        relative_postion = alph_to_vec(well) - initial_pos
        volume = initial_volume + dot_product(relative_postion, delta_vec)

        machine.goto_well(well)
        machine.dispense(volume, reagent)

@methods.register_method
def exponential_gradient(machine: Machine,
                 well_array,
                 reagent,
                 direction,
                 base,
                 initial_volume):
    std_basis = {
            "up": Vec2d(0, -1),
            "down": Vec2d(0, 1),
            "left": Vec2d(-1, 0),
            "right": Vec2d(1, 0)
            }

   if direction in ["left", "up"]:
       well_array = well_array.reverse()

    initial_pos = alph_to_vec(well_array[0])

    for well in well_array:
        relative_postion = alph_to_vec(well) - initial_pos
        volume = initial_volume * base ** dot_product(relative_postion, std_basis[direction])

        machine.goto_well(well)
        machine.dispense(volume, reagent)
