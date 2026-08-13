from flask import Flask, jsonify, Blueprint, request, session, Response
import asyncio
from .db import get_db, close_db
import threading
import time
import json
from .machine.serialcoms import ComsChannel, INITIAL_POSITION, ENABLE_MOTORS, DISABLE_MOTORS, ENABLE_PUMPS, DISABLE_PUMPS
from .machine.machine_state import Machine, Reagent_Mix
from .machine import kinematics as kine


def machine_aware_bp_factory(machine: Machine) -> Blueprint:
    bp = Blueprint('machine_aware_bp', __name__, url_prefix='/control')

    @bp.route('/home', methods=['POST'])
    def home():
        coms = machine.coms
        coms.send_home()
        while coms.most_recent_rx.code != INITIAL_POSITION:
            asyncio.run(coms.get_packet())
        initial_position_steps = coms.most_recent_rx.get_int_argvec()
        machine.coms.send_move_steps(*initial_position_steps)
        machine.current_position = machine.from_steps(*initial_position_steps)
        machine.home_offset = machine.current_position
        machine.position_known = True
        return jsonify({"data": "successful home"})

    @bp.route('/set_home_offset', methods=['POST'])
    def set_home_offset():
        if not machine.position_known:
            return home()
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

    @bp.route('/pump_action', methods=['POST'])
    def pump_action():
        data = request.get_json()
        volume_ul = float(data["volume"])
        id = int(data["id"])
        if volume_ul > 0:
            machine.dispense(volume=volume_ul, id=id)
        else:
            machine.aspirate(volume=volume_ul, id=id)
        return jsonify({"data": "successful pump action"})

    @bp.route('/move', methods=['POST'])
    def move():
        data = request.get_json()

        if data["move_context"] == "well":
            wellid = data["well_target"]
            machine.goto_well(wellid)
            return jsonify({"data": "went to well"})

        absolute_target: kine.MachinePosition

        if data["move_context"] == "jog":
            delta = list(data["delta"])
            absolute_target = machine.current_position + delta

        if data["move_context"] == "relative":
            relative_target = list(data["target"])
            absolute_target = machine.home_offset + relative_target
        if data["move_context"] == "absolute":
            relative_target = list(data["target"])
            absolute_target = relative_target

        machine.goto_pos(absolute_target)
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
        machine.methods.run_experiment(experiment)
        return jsonify({"data": "successful run!"})

    @bp.route('/simulate_experiment', methods=['POST'])
    def handle_experiment_simulation():
        data = request.get_json()
        db = get_db()
        db.execute("""
            DROP TABLE IF EXISTS tmp_pump_map;
        """)
        db.execute("""
            CREATE TABLE tmp_pump_map AS SELECT * FROM pumpMap
        """)
        db.commit()
        close_db()

        experiment = data["experiment"]
        forms = data["experiment"]["forms"]
        reagents_needed = []
        for formkey in forms:
            form = forms[formkey]
            reagent = form["reagent"]
            reagents_needed.append(reagent)
        id = 0
        for reagent in reagents_needed:
            db_update_pumps(reagent, id)
            id += 1
        output_plate = machine.methods.simulate_experiment(experiment)
        plate_data = output_plate.get_well_vol_dict()

        db = get_db()
        db.execute("""
                   DROP TABLE IF EXISTS pumpMap;
               """)
        db.execute("""
                   CREATE TABLE pumpMap
                   AS SELECT * FROM tmp_pump_map
                   """)
        db.commit()
        close_db()

        return jsonify({"data": plate_data})

    def monitor():
        prev = machine.coms.most_recent_rx
        while True:
            time.sleep(1)
            if machine.coms.most_recent_rx != prev:
                prev = machine.coms.most_recent_rx
                yield jsonify({"data": "hello"})

    @bp.route('/serial_stream', methods=['GET'])
    def return_serial_response_stream():
        return Response(monitor(), mimetype="text/event-stream")

    def db_update_pumps(reagent, id):
        db = get_db()
        print(f"inserting into db: {id} has {reagent}")
        db.execute("""
                    UPDATE pumpMap
                    SET reagent = ?
                    WHERE pumpID = ?
                    """,
                   (reagent, id))
        db.commit()
        close_db()

    @bp.route('/update_reagent', methods=["POST"])
    def update_pump_map():
        data = request.get_json()
        print(f"attempting to update reagents with: {data}")
        id = data["id"]
        reagent = data["reagent"]

        db_update_pumps(reagent, id)
        return jsonify({"data": f"updated pump {id} to contain {reagent}"})

    return bp
