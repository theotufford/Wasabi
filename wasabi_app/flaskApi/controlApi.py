import asyncio
import time
import json

from flask import Flask, jsonify, Blueprint, request, session, Response
from .db import get_db, close_db
from .machine.coms import codex
from .machine.utils import liq_handling_data, xy_to_alph
from .machine.coms.packet import code_packet, state_packet, make_int_vec_packet
from .machine import Machine, Kinematic_State, Vec3d


def machine_aware_bp_factory(machine: Machine) -> Blueprint:
    bp = Blueprint('machine_aware_bp', __name__, url_prefix='/control')

    @bp.route('/home', methods=['POST'])
    def home():
        machine.send_home()
        machine.got_home_complete.wait()
        machine.got_home_complete.clear()
        return jsonify({"data": "successful home"})

    @bp.route('/set_named_position', methods=['POST'])
    async def set_named_position():
        name = request.get_json()["name"]
        if not machine.position_known:
            await home()
        if name in machine.fixture.names:
            machine.fixture.named_positions[name] = machine.current_position
        return jsonify({"data": "successful waste position set"})

    @bp.route('/pump_action', methods=['POST'])
    def pump_action():
        data = request.get_json()
        volume_ul = float(data["volume"])
        id = int(data["id"])
        machine.dispense(volume=volume_ul, pumpid=id)
        return jsonify({"data": "successful pump action"})

    @bp.route('/move', methods=['POST'])
    def move():
        data = request.get_json()
        print(f"got jog directive: {data}")
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
        id = int(data["id"])
        machine.coms.queue_packet(make_int_vec_packet(codex.BUZZ, [id]))
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
        output = machine.methods.simulate_experiment(data["experiment"])
        return jsonify({
            "plate": output["plate"],
            "resources": output["resources"]
        })

    def monitor():
        pass

    @bp.route('/serial_stream', methods=['GET'])
    def return_serial_response_stream():
        return Response(None, mimetype="text/event-stream")

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

    @bp.route('/get_named_containers', methods=["POST"])
    def get_named_containers():
        return jsonify({"data": [*machine.named_containers.keys()]})

    return bp
