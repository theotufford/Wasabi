#probably depreciated but Im keeping this here if I change my mind and want to use fetch
from flask import Flask, jsonify, Blueprint, request, session
from .db import get_db
import threading
import time

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/getSession', methods=["GET", "POST"])
def returnSession():
    return jsonify(session)


@api_bp.route('/getExperiment', methods=["GET", "POST"])
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

