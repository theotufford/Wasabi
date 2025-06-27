import functools 
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from main.db import (get_db, pumpUpdate)

bp = Blueprint('home', __name__, url_prefix='/')



@bp.route('/', methods = ('GET','POST'))
def homePage():
    db = get_db()
    if request.method == "GET":
        msg = 0 
        experiment = request.get_json()[experiment]
        if experiment:
            msg = 1
        pumps  = json.loads(db.execute('SELECT pumpData FROM pumpatlas').fetchone()[0])
        return render_template('home/mainHomePage.htm', msg = msg, experiment=experiment, pumps=pumps)
    else:
        if request.get_json()['pump']:
            pump = request.get_json()['pump']
            pumpValue = request.get_json()['pumpValue']
            pumpUpdate({'name': pump, 'reagent': pumpValue})
            return "pumps updated"
        ##do pump stuff here because its the post request area 

