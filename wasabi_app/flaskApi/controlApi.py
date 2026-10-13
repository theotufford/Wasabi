import asyncio
import time
import json

from flask import Flask, jsonify, Blueprint, request, session, Response
from .db import get_db, close_db
from .machine.coms import codex
from .machine.coms.packet import code_packet, state_packet
from .machine import Machine, Kinematic_State, Vec3d


def machine_aware_bp_factory(machine: Machine) -> Blueprint:
    bp = Blueprint('machine_aware_bp', __name__, url_prefix='/control')

    @bp.route('/home', methods=['POST'])
    async def home():
        coms = machine.coms
        coms.send_packet(code_packet(codex.HOME))
        await machine.got_home.wait()
        return jsonify({"data": "successful home"})

    found_corner = asyncio.Event()

    @bp.route('/work_offset_finder', methods=['POST'])
    async def work_offset_finder():
        if not machine.position_known:
            await home()
        machine.goto_well("A1")
        await found_corner.wait()
        top_left = machine.current_position.position
        found_corner.clear()

        br_id = machine.plate.rows
        machine.goto_well(br_id)

        await found_corner.wait()
        bottom_right = machine.current_position.position
        found_corner.clear()

        machine.plate.set_plate_position(top_left, bottom_right)

    @bp.route('/work_offset_finder/found', methods=['POST'])
    def found_corner_resp():
        found_corner.set()

    @bp.route('/set_named_position', methods=['POST'])
    async def set_named_position():
        name = request.get_json()["name"]
        if not machine.position_known:
            await home()

        machine.named_positions[name] = machine.current_position
        return jsonify({"data": "successful waste position set"})

    @bp.route('/pump_action', methods=['POST'])
    def pump_action():
        data = request.get_json()
        volume_ul = float(data["volume"])
        id = int(data["id"])
        if volume_ul > 0:
            machine.handle_liquids(volume=volume_ul, id=id)
        else:
            machine.aspirate(volume=volume_ul, id=id)
        return jsonify({"data": "successful pump action"})

    @bp.route('/move', methods=['POST'])
    def move():
        data = request.get_json()

        if data["move_context"] == "named":
            target = data["target_name"]
            machine.goto_named(target)
            return jsonify({"data": "went to well"})

        if data["move_context"] == "well":
            wellid = data["well_target"]
            machine.goto_well(wellid)
            return jsonify({"data": "went to well"})

        absolute_target: Kinematic_State

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
        return jsonify({"data": f"successful {data["move_context"]} move"})

    @bp.route('/buzz', methods=['POST'])
    def buzz_pump():
        data = request.get_json()
        id = data["id"]
        machine.coms.send_packet(code_packet(codex.BUZZ))
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

    @bp.route('/purge_pumps', methods=["POST"])
    def purge_pump():
        data = request.get_json()
        id = data["id"]
        direction = data["direction"]
        line_volume = machine.settings(
        )["motors"]["pumps"][id]["line_volume_uL"]
        if direction == "forward":
            machine.goto_well("waste")
            machine.handle_liquids(volume=line_volume, id=id)
        else:
            machine.aspirate()
        db_update_pumps("empty", id)

    @bp.route('/update_reagent', methods=["POST"])
    def update_pump_map():
        data = request.get_json()
        print(f"attempting to update reagents with: {data}")
        id = data["id"]
        reagent = data["reagent"]

        db_update_pumps(reagent, id)
        return jsonify({"data": f"updated pump {id} to contain {reagent}"})

    return bp
