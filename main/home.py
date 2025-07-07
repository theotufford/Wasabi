import functools 
import json
from .slicer import *

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from main.db import (get_db, pumpUpdate)

from main.agent import *

bp = Blueprint('home', __name__, url_prefix='/home')

@bp.route('/', methods = ['GET','POST'])
def homePage():
    db = get_db()
    reagents = []
    if request.method == "GET":
        experiment = None
        try:
            experimentTitle = request.args.get('title') 
            version = request.args.get('version') 
            experiment = returnExperimentbyVersion({"title": experimentTitle, "version": version})
            print(experiment["data"])
        except Exception as e:
            print(e)
        if experiment:
            data = json.loads(experiment["data"])
            for field in data:
                if "form" in field:
                    reagents.append(data[field]["reagent"])
                    print(f"reagents:{reagents}")
        pumps  = db.execute('SELECT * FROM pumpMap').fetchall()
        for row in pumps:
            print(f"pump: {row['pumpID']}")
            print(f"reagent: {row['reagent']}")
        return render_template('home/home.htm', reagents = reagents, experiment=experiment, pumps=pumps)
    else:
        experimentTitle = request.args.get('title') 
        version = request.args.get('version') 
        rawData = returnExperimentbyVersion({"title": experimentTitle, "version": version})['data']
        data = json.loads(rawData)
        gcode = translate(data)
        return "successful run init";
