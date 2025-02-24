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
    function_args = request.get_json()['args']

    #print(splitter(f"target: {function_target}\n arguments: {function_args}"))
    return globals()[function_target](function_args)

def render_form(data): #gets the parameters for the form from the request and renders the form template with them
    db = get_db()
    pumpContents = json.loads(db.execute('SELECT pumpData FROM pumpatlas').fetchone()[0])
    print(splitter(f"render_form\n{data}\n{pumpContents}"))

    if(data == "empty"):
        return render_template("programmer/formBody.htm", pumpContents = pumpContents)
    elif(data is not None):
        return render_template("programmer/formBody.htm", pumpContents = pumpContents, renderData = data )
    else:
        pass

def getMethodForm(data):
    resp = render_template("programmer/methodTemplates.htm", method = data["method"])
    return resp

def dump(data): # dumps all of the construction information for each form in the current experiment to the session
    pass
