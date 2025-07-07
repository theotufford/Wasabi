import functools
from datetime import date 
import json
from flask import (
        Blueprint, flash, g, redirect, current_app, render_template, request, session, url_for
        )

from main.db import get_db
bp = Blueprint('programmer', __name__, url_prefix='/program')

@bp.route('/', methods=["GET"])
def programmer():
    db = get_db()
    with current_app.open_resource('./static/resources/config.json') as f:
        config = f.read()
        plates = json.loads(config)["machineInfo"]["plates"]
    experiment = request.args.get('experiment') or None
    if experiment:
        print(f"attempting to render {experiment} ")
    return render_template("programmer/programmer.htm", plates = plates, experiment = experiment) 
