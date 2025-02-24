import functools
from datetime import date 
import json
from flask import (
        Blueprint, flash, g, redirect, current_app, render_template, request, session, url_for
        )

from main.db import (get_db, pumpUpdate)
bp = Blueprint('programmer', __name__, url_prefix='/program')

@bp.route('/', methods=["GET"])
def programmer():
    db = get_db()
    with current_app.open_resource('./static/resources/config.json') as f:
        plates = json.loads(f.read())["machineInfo"]["plates"]
    experiments = db.execute("SELECT title FROM experiments ").fetchall()
    pumps = db.execute("SELECT pumpData FROM pumpAtlas ").fetchall()
    return render_template("programmer/programmer.htm", plates = plates, pumps = pumps, experiment_titles = experiments) 
