from flask import flask, jsonify, blueprint, request, session
from .db import get_db
import threading
import time
import json
from .machine.serialcoms import comschannel, initial_position
from .machine.machine_state import machine
from .machine import kinematics as kine


def machine_aware_bp_factory(machine_global: machine) -> blueprint:
    bp = blueprint('machine_aware_bp', __name__)

    @bp.route('/home', methods=["post"])
    def home():
        coms = machine_global.coms
        coms.send_home()
        coms.await_confirm()
        coms.send_home()
        while true:
            coms.get_packet()
            if coms.most_recent_rx.code == initial_position:
                returned_pos_steps = coms.most_recent_rx.get_int_argvec()
                initial_a = returned_pos_steps[0]
                initial_b = returned_pos_steps[1]
                initial_z = returned_pos_steps[2]
                a_mot_angle = initial_a / machine_global.a_steps_per_rad
                b_mot_angle = initial_b / machine_global.b_steps_per_rad
                z_position = initial_z / machine_global.z_steps_per_mm
                xy_pos = machine_global.solve_5bar_fk(a_mot_angle, b_mot_angle)
                pos = kine.machineposition()
                pos.x = xy_pos.x
                pos.y = xy_pos.y
                pos.z = z_position
                pos.alpha = a_mot_angle
                pos.beta = b_mot_angle
                machine_global.home_offset = pos
                coms.send_move_steps(initial_a, initial_b, initial_z)
                break
        coms.await_confirm()
        machine_global.generate_plate_map()
        print(f"platemap: {machine_global.abs_plate_map}")
        input()
        machine_global.move_to_well("a1")

    return bp
