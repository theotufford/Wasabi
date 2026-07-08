from flask import Flask, jsonify, Blueprint, request, session
from .db import get_db
import threading
import time
import json
from .machine.serialcoms import ComsChannel, INITIAL_POSITION
from .machine.machine_state import Machine
from .machine import kinematics as kine


def machine_aware_bp_factory(machine: Machine) -> Blueprint:
    bp = Blueprint('machine_aware_bp', __name__)

    @bp.route('/home', methods=['POST'])
    def home():
        coms = machine.coms
        coms.send_home()
        while coms.most_recent_rx.code != INITIAL_POSITION:
            coms.get_packet()
        initial_position_steps = coms.most_recent_rx.get_int_argvec()
        machine.coms.send_move_steps(*initial_position_steps)
        machine.home_offset = machine.from_steps(*initial_position_steps)
        machine.current_position = machine.home_offset
        machine.position_known = True
        print(f"set home offset: {machine.home_offset}")
        machine.populate_plate_map()
        return jsonify({"data": "successful home"})

    @bp.route('/jog', methods=['POST'])
    def jog():
        data = request.get_json()
        delta = list(data["delta"])
        print(f"delta: {delta}")
        print(f"initial: {machine.current_position}")
        target = machine.current_position + delta
        print(f"target: {target}")
        machine.goto_pos(target)
        return jsonify({"data": "successful jog"})

    return bp
