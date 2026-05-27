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
    else:  # if no version is given the highest versioned instance is returned
        resp = db.execute(
            """
                SELECT * FROM experiments
                WHERE title = ?
                ORDER BY version DESC
                LIMIT 1
                """, (data['title'],)).fetchone()

    return resp


bp = Blueprint('dataApi', __name__, url_prefix='/dataApi')


@bp.route('/deleteExperiment', methods=["POST"])
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
    print(f"deleted: {experiment['title']}")
    db.commit()


@bp.route('/fetchExperiment', methods=["POST"])
def fetchExperiment():
    data = request.get_json()
    print(data)
    dbRepsonse = getExperiment(data)
    try:
        experiment = jsonify(dict(dbRepsonse))
        print(f"{dict(dbRepsonse)=}")
        return experiment
    except:
        return 'oops'


def reagentLibUpdate(experiment):
    db = get_db()
    returnVal = "no update"  # if not altered there was no update
    for form in experiment.get('forms').values() or []:
        reagent = form.get("reagent")
        if reagent is None:
            continue
        reagentRecord = db.execute(
            '''
                SELECT reagent
                FROM reagentLib
                WHERE reagent IS ?
            ''', (reagent,)).fetchone()
        if reagentRecord:
            continue
        db.execute('INSERT INTO reagentLib (reagent) VALUES (?)', (reagent,))
        returnVal = "updatedReagents"
    db.commit()
    return returnVal


@bp.route('/saveExperiment', methods=["POST"])
def saveExperiment():
    data = request.get_json()
    print(f"data :{data}")
    if not data.get('forms'):
        print('no data!')
        return jsonify({"empty": ""})

    db = get_db()
    autoSave = data["autosave"]
    title = data["title"]
    experimentJson = json.dumps(data)

    dbFetch = getExperiment({"title": title})
    selected = {}
    if dbFetch is not None:
        selected = dict(dbFetch)
    version = selected.get("version") or 0

    reagentLibUpdate(data)
    if selected.get('data') == experimentJson:  # duplicate protection
        print('trying to save duplicate, aborting')
        return jsonify('trying to save a perfect duplicate')
    if not autoSave:
        if selected is not {}:
            version = version+1
        db.execute("""
                   INSERT INTO experiments (data, title, version) VALUES (?, ?, ?)
                   """,
                   (experimentJson, title, version))
        db.commit()
        return jsonify({"version": version})
    db.execute("""
               UPDATE experiments 
               SET data = ?
               WHERE (title = ?)
               """, (experimentJson, "autosave"))
    db.commit()
    return jsonify({"status": 1})


@bp.route('/experiment_dump', methods=["POST"])
def experiment_dump():
    db = get_db()
    title_version_array = []
    dump = db.execute("""
               SELECT title, version
               FROM experiments
               ORDER BY created
               """).fetchall()
    for row in dump:
        title_version_array.append(dict(row))
    return jsonify({"data": title_version_array})

# @bp.route('/run_experiment', methods=["POST"])
# def run_experiment(experimentTitle):
#     db = get_db()


# this is sort of cursed that this is using post instead of get but im lazy
@bp.route('/get_pump_map', methods=["POST"])
def get_current_reagents():
    db = get_db()
    reagents_by_id = {}
    dump = db.execute("""
                      SELECT pumpID, reagent
                      FROM pumpMap
                      """).fetchall()
    for row in dump:
        rowdict = dict(row)
        reagents_by_id[rowdict["pumpID"]] = rowdict["reagent"]
    return jsonify({"data": reagents_by_id})


@bp.route('/current_reagents', methods=["POST"])
def update_pump_map(data):
    id = data.get('id')
    reagent = data.get('new_reagent')
    if id is None or reagent is None:
        return jsonify({"data": "data error!"})

    db = get_db()
    db.execute("""
                UPDATE pumpMap
                SET reagent = ?
                WHERE pumpID = ?
                """,
               (reagent, id))
    return jsonify({"data": f"updated pump {id} to contain {reagent}"})
