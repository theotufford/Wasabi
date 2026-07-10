from flask import Flask, jsonify, Blueprint, request, session
from .db import get_db
import threading
import time
import json
from .machine.serialcoms import ComsChannel, INITIAL_POSITION, ENABLE_MOTORS, DISABLE_MOTORS, ENABLE_PUMPS, DISABLE_PUMPS
from .machine.machine_state import Machine
from .machine import kinematics as kine
from .machine.parser import run_experiment


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
        return jsonify({"data": "successful home"})

    @bp.route('/set_home_offset', methods=['POST'])
    def set_home_offset():
        if not machine.position_known:
            return jsonify({"data": "machine position not currently known!!"})
        machine.home_offset = machine.current_position

    @bp.route('/mot_enable', methods=['POST'])
    def mot_enable():
        coms = machine.coms
        data = request.get_json()
        target = data["target"]
        value = data["value"]
        code = None
        if target == "motors":
            code = ENABLE_MOTORS if value == "enable" else DISABLE_MOTORS
            machine.position_known = False
        if target == "pumps":
            code = ENABLE_PUMPS if value == "enable" else DISABLE_PUMPS
        coms.send_code(code)
        coms.await_confirm()

        return jsonify({"data": {"target": target, "status": value}})

    @bp.route('/jog', methods=['POST'])
    def jog():
        data = request.get_json()
        print("got jog with data: ", data)
        delta = list(data["delta"])
        target = machine.current_position + delta
        machine.goto_pos(target)
        return jsonify({"data": "successful jog"})

    @bp.route('/buzz', methods=['POST'])
    def buzz_pump():
        data = request.get_json()
        id = data["id"]
        machine.coms.send_buzz(id)
        return jsonify({"data": f"buzzed id:{id}"})

    @bp.route('/run_experiment', methods=['POST'])
    def handle_experiment_run():
        data = request.get_json()
        experiment = data["experiment"]
        run_experiment(machine, experiment)
        return jsonify({"data": "successful run!"})

    return bp
