from flask import Flask, jsonify, Blueprint, request, session
from .db import get_db, close_db
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

    close_db()
    return resp


bp = Blueprint('dataApi', __name__, url_prefix='/dataApi')


@bp.route('/deleteExperiment', methods=["POST"])
def deleteExperiment():
    data = request.get_json()
    db = get_db()
    db.execute("""
               DELETE FROM experiments
               WHERE title = ?
               AND version = ?
               """, (
        data['title'],
        data['version']))
    db.commit()
    close_db()
    return jsonify({"data": f"deleted {data['title']} v{data['version']} "})


@bp.route('/fetchExperiment', methods=["POST"])
def fetchExperiment():
    data = request.get_json()
    print(data)
    dbRepsonse = getExperiment(data)
    if dbRepsonse is None:
        return jsonify({"failure": True})
    exp = json.loads(dict(dbRepsonse)["data"])
    print(f"exp: {exp}")
    return jsonify(exp)


@bp.route('/saveExperiment', methods=["POST"])
def saveExperiment():
    data = request.get_json()
    print(f"saving {data}")
    db = get_db()
    autoSave = data["autosave"]
    title = data["title"]
    version = data["version"]
    experimentJson = json.dumps(data)
    dbFetch = getExperiment({"title": title})
    selected = {}
    if dbFetch is not None:
        selected = dict(dbFetch)
    if selected.get('data') == experimentJson:  # duplicate protection
        print('trying to save duplicate, aborting')
        return jsonify('trying to save a perfect duplicate')
    if not autoSave:
        db.execute("""
                   INSERT INTO experiments
                   (data, title, version)
                   VALUES (?, ?, ?)
                   """,
                   (experimentJson, title, version))
        db.commit()
        close_db()
        return jsonify({"version": version})
    db.execute("""
               UPDATE experiments
               SET data = ?
               WHERE (title = ?)
               """, (experimentJson, "autosave"))
    db.commit()
    close_db()
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
    close_db()
    return jsonify({"data": title_version_array})


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
    close_db()
    return jsonify({"data": reagents_by_id})


@bp.route('/get_authors', methods=["POST"])
def get_authors():
    db = get_db()
    authors = []
    dump = db.execute("""
                      SELECT name
                      FROM authors
                      """).fetchall()
    close_db()
    for row in dump:
        rowdict = dict(row)
        print(f"appending author to return: {rowdict}")
        authors.append(rowdict["name"])
    print(f"returning authors: {authors}")
    close_db()
    return jsonify({"data": authors})


@bp.route('/new_author', methods=["POST"])
def new_author():
    db = get_db()
    data = request.get_json()
    print(f"making new author: {data}")
    db.execute("""
               INSERT INTO authors (name)
               VALUES (?)
               """,
               (data["name"],))
    db.commit()
    close_db()
    return jsonify('success')


@bp.route('/update_reagent', methods=["POST"])
def update_pump_map():
    data = request.get_json()
    print(f"attempting to update reagents with: {data}")

    id = data["id"]
    reagent = data["reagent"]

    db = get_db()
    db.execute("""
                UPDATE pumpMap
                SET reagent = ?
                WHERE pumpID = ?
                """,
               (reagent, id))
    db.commit()
    close_db()
    return jsonify({"data": f"updated pump {id} to contain {reagent}"})
