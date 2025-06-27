import json
from flask import (
    Blueprint, redirect, current_app, render_template, request, session, url_for, jsonify
)
from main.db import get_db 
bp = Blueprint('agent', __name__, url_prefix='/agent')

def splitter(message):
    return f'\n-------------------\n{message}\n-------------------\n' 
@bp.route('/', methods=["POST"])
def agent_handler(): # handle input from json calls and run the function from the global scope that they reference
    function_target = request.get_json()['function_target'] # get target function name
    function_args = request.get_json().get('args') # get target function args
    #print(splitter(f"target: {function_target}\n arguments: {function_args}"))
    functionReturn = globals()[function_target](function_args) # run target function with args via return 
    print(f"called {function_target} with {function_args}, function returned: {functionReturn}")
    return functionReturn
def render_form(data): #gets the parameters for the form from the request and renders the form template with them
    db = get_db()
    reagentResp = db.execute('SELECT reagent FROM reagentLib').fetchall() # grab all of the selectable reagents
    print("rendering form")
    reagentLib = []
    for reagent in reagentResp:
        reagentLib.append(reagent[0])
    if data is None:
        data = {"empty":"empty"}
    return render_template("programmer/formBody.htm", reagentLib = reagentLib, renderData = data )

def getMethodForm(data): # handler to return specific method sub forms
    resp = render_template("programmer/methodTemplates.htm", method = data["method"], renderData = data.get("renderData"))
    return resp

def returnExperimentbyVersion(data): # returns some experiment by a specific version
    db = get_db()
    print(data)
    if data.get('version'):
        resp = db.execute( """
        SELECT * FROM experiments
            WHERE title = ? 
            AND version = ?
        """, (data['title'], data['version'],)).fetchone()
    else: # if no version is given the highest versioned instance is returned 
        resp = db.execute( """
        SELECT * FROM experiments
            WHERE title = ?
            ORDER BY version DESC
            LIMIT 1
        """, (data['title'],)).fetchone()
    print(f"{resp=}")
    return resp

def reagentLibUpdate(data):
    db = get_db()
    print("updating reagents")
    returnVal = "noUpdate"
    for key, value in data.items():
        if "form" in key:
            if value.get("reagent"):
                reagent = value.get("reagent")
                print(f"selected reagent: {reagent}")
                resp = db.execute('SELECT reagent FROM reagentLib WHERE reagent IS ? ', (reagent,)).fetchone()
                print(f"{resp=}")
                if resp is None:
                    db.execute('INSERT INTO reagentLib (reagent) VALUES (?)', (reagent, ))
                    db.commit()
                    returnVal = "updatedReagents"
    print(f"reagent return value:{returnVal}")
    return returnVal

def dump(data): # dumps all of the construction information for each form in the current experiment to the database
    db = get_db()
    session['autosave'] = data
    experimentJson = json.dumps(data)
    resp = returnExperimentbyVersion(data)
    version = 0
    returnVal = reagentLibUpdate(data)
    if resp:
        if resp['data'] == experimentJson:
            return jsonify('trying to save a perfect duplicate')
        version = resp['version'] + 1
        print(f"version: {resp['version']}")
    db.execute(
        'INSERT INTO experiments (data, title, version) VALUES (?, ?, ?)', (experimentJson, data['title'], version)
        )
    db.commit()
    return jsonify("dumped!")


def getExperiment(data):
    title = data.get('title')
    if title == "autosave":
        data = session.get('autosave')
        if data:
            return data
        else:
            return jsonify("no autosave")
    resp = returnExperimentbyVersion(data)
    if resp:
        resp = resp['data']
    else: 
        resp = "not found"
    return resp


def returnUrl(url):
    session['returnUrl'] = url
    return jsonify( 'url added: ' + url )

def getFromSession(term):
    return  session.get(term) 

def deleteExperiment(data):
    db = get_db()
    db.execute( " DELETE FROM experiments WHERE title = ? AND version = ?", (data['title'],data['version']))
    db.commit()
    print(splitter(f'{data["title"]}_v{data["version"]} deleted'))
    return jsonify( f'{data["title"]}_v{data["version"]} deleted' )

def run_experiment(data):
    db = get_db()
    pumps = json.loads(db.execute('SELECT pumpData FROM pumpatlas').fetchone()[0]) #
    missing_contents  = [data[form]["contents"] for form in data if data[form] not in pumpatlas]
    return jsonify( "run error" )
