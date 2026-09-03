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
def get_current_pump_map():
    db = get_db()
    reagnets_by_pumpid = {}
    dump = db.execute("""
                      SELECT pumpID, reagent
                      FROM pumpMap
                      """).fetchall()
    for row in dump:
        rowdict = dict(row)
        reagnets_by_pumpid[rowdict["pumpID"]] = rowdict["reagent"]
    close_db()
    return jsonify({"data": reagnets_by_pumpid})


@bp.route('/add_reagent', methods=["POST"])
def add_reagent():
    db = get_db()
    data = request.get_json()
    metadata = data["metadata"]
    name = data["name"]
    db.execute("""
               INSERT INTO reagentLib (name, metadata)
               VALUES (?, ?)
               """,
               (name, json.dumps(metadata)))
    db.commit()
    close_db()
    return jsonify('success')


@bp.route('/modify_reagent', methods=["POST"])
def modify_reagent():
    data = request.get_json()
    metadata = data["metadata"]
    name = data["name"]
    db = get_db()
    db.execute("""
               UPDATE experiments
               SET metadata = ?
               WHERE (name = ?)
               """, (json.dumps(metadata), name))
    db.commit()
    close_db()
    return jsonify('success')


@bp.route('/delete_reagent', methods=["POST"])
def delete_reagent():
    data = request.get_json()
    db = get_db()
    db.execute("""
               DELETE FROM reagentLib
               WHERE name = ?
               """, (
        data["name"],))
    db.commit()
    close_db()
    return jsonify({"data": f"deleted {data['name']}"})


@bp.route('/get_reagent', methods=["POST"])
def get_reagent():
    data = request.get_json()
    name = data["name"]
    db = get_db()
    value = db.execute("""
                      SELECT metadata
                      FROM reagentLib
                      WHERE name = ?
                      """, (name,)).fetchone()
    if value is None:
        return jsonify({"failure": True})
    close_db()
    return jsonify({"data": json.loads(dict(value)["metadata"])})


@bp.route('/dump_reagents', methods=["POST"])
def dump_reagents():
    db = get_db()
    dump = db.execute("""
                       SELECT * FROM reagentLib
                       """).fetchall()
    dump_dict = {k: v for k, v in dict(dump).items() if k is not None}
    print(dump_dict)
    return jsonify({"data": dump_dict})


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
