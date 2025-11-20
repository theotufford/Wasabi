from flask import Flask, jsonify, Blueprint, request, session
from .db import get_db
import threading
import time
import json
def getExperiment(data):
    db = get_db()
    if data.get('version') is not None:
        resp = db.execute( 
                          """
                          SELECT * FROM experiments
                          WHERE title = ? 
                          AND version = ?
                          """, (data['title'], data['version'],)).fetchone()
    else: # if no version is given the highest versioned instance is returned 
        resp = db.execute(
                """
                SELECT * FROM experiments
                WHERE title = ?
                ORDER BY version DESC
                LIMIT 1
                """, (data['title'],)).fetchone()
    if resp is not None:
        for key in resp.keys():
          print(f"{key} : {resp[f'{key}']}")
    print(f"database {resp=}")
    return resp

bp = Blueprint('dataApi', __name__, url_prefix='/dataApi')

@bp.route('/deleteExperiment', methods = ["POST"])
def deleteExperiment(experiment):
    db = get_db()
    db.execute("""
               DELETE FROM experiments
               WHERE title = ?
               AND version = ?
               """, (
                   experiment['title'],
                   experiment['version']
                   )
               )
    print( f"deleted: {experiment['title']}")
    db.commit()

@bp.route('/fetchExperiment', methods = ["POST"])
def fetchExperiment():
    data = request.get_json()
    print(data)
    experiment = jsonify(dict(getExperiment(data)))
    return experiment

@bp.route('/dbDump', methods = ["POST"])
def dbDump():
    db = get_db()
    expArray = []
    dump = db.execute("""
               SELECT title, version 
               FROM experiments
               ORDER BY title
               """).fetchall()
    for row in dump:
        expArray.append(dict(row))
        print(dict(row))
    return jsonify({"data":expArray})
@bp.route('/run_experiment', methods = ["POST"])
def run_experiment(experimentTitle):
    db = get_db()
    if type(experimentTitle) is not str:
        raise ValueError("this function wants an experiment title, you gave it:\"{experimentTitle}\" ")
    missing_contents  = [experiment[form]["contents"] for form in experiment if data[form]["contents"] not in pumpatlas]
    if len(missing_contents) > 0:
        return jsonify( f"run error, missing contents: {missing_contents}" )
