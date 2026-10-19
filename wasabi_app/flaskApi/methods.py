from datetime import datetime
from flask import Flask, jsonify, Blueprint, request, session
from typing import Literal
from .machine import Machine, MethodLibrary
from .machine.kinematics import Vec2d, dot_product
from .machine.utils import alph_to_vec, get_linear_well_array_height, get_linear_well_array_width, xy_to_alph

methods = MethodLibrary()


@methods.register_method
def purge(machine: Machine, volume: float, pump_id: int):
    machine.goto_well("waste")
    machine.dispense(volume, id=pump_id)


@methods.register_method
def volume_map(machine: Machine,
               volume_map: dict,
               reagent):
    for wellid in volume_map:
        volume = volume_map[wellid]
        if volume == 0:
            continue
        machine.goto_well(wellid)
        machine.dispense(volume, reagent=reagent)


@methods.register_method
def await_manual_continue(machine: Machine, action_prompt: str = "no prompt given"):
    machine.stall_for_confirm(action_prompt)
