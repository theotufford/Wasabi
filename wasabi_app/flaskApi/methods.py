from datetime import datetime
from flask import Flask, jsonify, Blueprint, request, session
from typing import Literal
from .machine import Machine, MethodLibrary
from .machine.kinematics import Vec2d, dot_product
from .machine.utils import alph_to_vec, get_linear_well_array_height
from .machine.method_arg_classes import Volume, Plate_Map, Named_Container, Reagent, Wellid

methods = MethodLibrary()


@methods.register_method
def purge(machine: Machine,
          volume: float,
          pump_id: int):
    machine.goto_named("waste")
    machine.dispense(volume, id=pump_id)


@methods.register_method
def volume_map(machine: Machine,
               volume_map: Plate_Map[Volume],
               reagent: Reagent):
    for wellid in volume_map:
        volume = volume_map[wellid]
        if volume == 0 or volume == "":
            continue
        volume = float(volume_map[wellid])
        machine.goto_well(wellid)
        machine.dispense(volume, reagent=reagent)


@methods.register_method
def volume_map_from_aspiration_source(machine: Machine,
                                      pumpid: int,
                                      named_location: Named_Container,
                                      volume_map: Plate_Map[Volume]):
    total_volume = 0
    for wellid in volume_map:
        total_volume += volume_map[wellid]

    machine.goto_named(named_location)
    machine.aspirate(total_volume, pumpid)
    for wellid in volume_map:
        volume = volume_map[wellid]
        if volume == 0 or volume == "":
            continue
        volume = float(volume_map[wellid])
        machine.goto_well(wellid)
        machine.dispense(volume, pumpid=pumpid)


@methods.register_method
def discard_volume_by_map(machine: Machine,
                          pumpid: int,
                          volume_map: Plate_Map[Volume]):

    for wellid in volume_map:
        volume = float(volume_map[wellid])
        if volume == 0:
            continue
        machine.goto_well(wellid)
        machine.aspirate(volume, pumpid=pumpid)
        machine.goto_named("waste")
        machine.dispense(volume, pumpid=pumpid)


@methods.register_method
def await_manual_continue(machine: Machine, action_prompt: str = "no prompt given"):
    machine.stall_for_confirm(action_prompt)


@methods.register_method
def change_reagent_in_pump(machine: Machine, to_discard: Reagent, new_reagent: Reagent):
    machine.goto_named("waste")
    machine.stall_for_confirm(
        f"connect {new_reagent} into pump, enter to confirm")
    machine.swap_reagent(to_discard, new_reagent)
