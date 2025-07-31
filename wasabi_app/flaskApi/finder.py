import json
from flask import (
    Blueprint, redirect, current_app, render_template, request, session, url_for, jsonify
)
from flaskApi.db import (get_db)
bp = Blueprint('finder', __name__, url_prefix='/finder')

def splitter(message):
    return f'\n-------------------\n{message}\n-------------------\n' 

@bp.route('/', methods=["GET"])
def finder():
    db = get_db()
    experiments = db.execute(
        """
        SELECT MAX(version) AS version, title
        FROM experiments
        GROUP BY title
        """
    ).fetchall()
    for experiment in experiments:
        print(splitter(f"{experiment['title']}\n{experiment['version']}"))
    with current_app.open_resource('./static/resources/config.json') as f:
        config = f.read()
        plates = json.loads(config)["machineInfo"]["plates"]
    return render_template("finder/finderBody.htm", plates = plates, experiments = experiments)
@bp.route('/display', methods=["POST"])
def display():
    experiment = request.get_json()['experiment']
    return render_template("finder/plateDisplay.htm", experiment = experiment )
