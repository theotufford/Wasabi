import json
from flask import (
    Blueprint, redirect, current_app, render_template, request, session, url_for, jsonify
)
from main.db import (get_db)
bp = Blueprint('agent', __name__, url_prefix='/agent')

def splitter(message):
    return f'\n-------------------\n{message}\n-------------------\n' 
@bp.route('/', methods=["POST"])
def agent_handler():
    function_target = request.get_json()['function_target']
    function_args = request.get_json().get('args')
    #print(splitter(f"target: {function_target}\n arguments: {function_args}"))
    return globals()[function_target](function_args)

def render_form(data): #gets the parameters for the form from the request and renders the form template with them
    db = get_db()
    pumps = json.loads(db.execute('SELECT pumpData FROM pumpatlas').fetchone()[0])
    print(splitter(f"render_form\n{data}\n{pumps}"))
    if(data is None):
        return render_template("programmer/emptyformBody.htm", pumps = pumps)
    elif(data is not None):
        return render_template("programmer/formBody.htm", pumps = pumps, renderData = data )
    else:
        return("data is empty")

def getMethodForm(data):
    resp = render_template("programmer/methodTemplates.htm", method = data["method"], renderData = data.get("renderData"))
    return resp

def returnExperimentbyVersion(data):
    print(data)
    db = get_db()
    if data.get('version'):
        resp = db.execute( """
        SELECT * FROM experiments
                WHERE title = ? AND version = ?
        """, (data['title'], data['version'],)).fetchone()
    else:
        resp = db.execute( """
        SELECT title, data, version FROM experiments
            WHERE title = ?
            ORDER BY version DESC
            LIMIT 1
        """, (data['title'],)).fetchone()
    return resp


def dump(data): # dumps all of the construction information for each form in the current experiment to the session
    db = get_db()
    if (data.get('autosave')):
        session['autosave'] = data
        return ("autosaved!")
    experimentJson = json.dumps(data)
    print(experimentJson)
    resp = returnExperimentbyVersion(data)
    version = 0
    if resp:
        version = resp['version'] + 1
        print(f"version: {resp['version']}")

    db.execute(
        'INSERT INTO experiments (data, title, version) VALUES (?, ?, ?)', (experimentJson, data['title'], version)
        )
    db.commit()
    return("dumped!")

def getExperiment(data):
    title = data.get('title')

    if title == "autosave":
        data = session.get('autosave')
        if data:
            return jsonify(data)
        else:
            return jsonify("no autosave")

    db = get_db()
    resp = returnExperimentbyVersion(data)
    if resp:
        resp = resp['data']
    print(f'db response: {resp}')
    return resp


def returnUrl(url):
    session['returnUrl'] = url
    return 'url added: ' + url
def getFromSession(term):
    return session.get(term)
