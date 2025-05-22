import json
from flask import (
    Blueprint, redirect, current_app, render_template, request, session, url_for, jsonify
)
from main.db import (get_db)
bp = Blueprint('translator', __name__, url_prefix='/translator')

def splitter(message):
    return f'\n-------------------\n{message}\n-------------------\n' 

alph = "abcdefghijklmnopqrstuvwxyz".split("")
invAlph = alph.reverse()


@bp.route('/', methods=["POST"])
def translator():
    #get target experiment from request
    experiment = request.get_json()['experiment']
    version = experiment["version"]
    title = experiment["title"]
    #get experiment data from database
    db = get_db()
    expdata = json.loads(db.execute( 
    """
        SELECT data FROM experiments
        WHERE title = ? 
        AND version = ?
    """, 
    (title, version,)).fetchone())

    wellmap = {} #end output dictionary of wells and and array of their contents
    for item in expdata.keys(): #iterate through experiment data keys 
        form = expdata[item] 
        if !(form.key().contains("form")):#make sure that key is a form and not the title or something else
            return
        else:
            from = form['from']
            to = form['to']
            colEdge = [from[0:], to[0:]]
            rowEdge = [from[0], to[0]]
            wellrange = abs()
