from datetime import datetime
from flask import Flask, jsonify, Blueprint, request, session
from typing import Literal
from .machine import Machine, MethodLibrary
from .machine.kinematics import Vec2d, dot_product
from .machine.utils import alph_to_vec, get_linear_well_array_height
from .machine.method_arg_classes import Volume, Plate_Map, Named_Container, Reagent, Wellid, Volume_Map

methods = MethodLibrary()


@methods.register_method
def purge(machine: Machine,
          volume: float,
          pump_id: int):
    machine.goto_named("waste")
    machine.dispense(volume, id=pump_id)


@methods.register_method
def volume_map(machine: Machine,
               volume_map: Volume_Map,
               reagent: Reagent):
    for wellid in volume_map:
        volume = volume_map[wellid]
        if volume == 0 or volume == "":
            continue
        volume = float(volume_map[wellid])
        machine.goto_well(wellid)
        machine.dispense(volume, reagent=reagent)


@methods.register_method
def dispense_into_container(machine: Machine,
                            named_location: Named_Container,
                            reagent: Reagent,
                            volume: Volume):
    machine.goto_named(named_location)
    machine.dispense(volume, reagent=reagent)


@methods.register_method
def transfer_from_well_to_plate(machine: Machine,
                                pumpid: int,
                                source: Wellid,
                                volume_map: Volume_Map):
    total = volume_map.get_value_sum()
    machine.goto_well(source)
    machine.aspirate(total, pumpid=pumpid)
    for wellid in volume_map:
        volume = volume_map[wellid]
        if volume == 0 or volume == "":
            continue
        volume = float(volume_map[wellid])
        machine.goto_well(wellid)
        machine.dispense(volume, pumpid=pumpid)


@methods.register_method
def transfer_from_container_to_container(machine: Machine,
                                         pumpid: int,
                                         source: Named_Container,
                                         sink: Named_Container,
                                         volume: Volume):
    machine.goto_named(source)
    machine.aspirate(volume, pumpid)
    print(f"{machine.get_state_data()}")
    machine.goto_named(sink)
    machine.dispense(volume, pumpid=pumpid)
    print(f"{machine.get_state_data()}")


@methods.register_method
def transfer_from_container_to_plate(machine: Machine,
                                     pumpid: int,
                                     named_location: Named_Container,
                                     volume_map: Volume_Map):
    total_volume = volume_map.get_value_sum()
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
                          volume_map: Volume_Map):

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
