#probably depreciated but Im keeping this here if I change my mind and want to use fetch
from flask import Flask, jsonify, Blueprint, request, session
from .db import get_db
import threading
import time
import json

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/getSession', methods=["GET", "POST"])
def returnSession():
    return jsonify(session)

@api_bp.route('/getExperiment', methods=["GET", "POST"])
def getExperiment(data):
    db = get_db()
    print(data)
    if data.get('version'):
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
    print(f"{resp=}")
    return resp

