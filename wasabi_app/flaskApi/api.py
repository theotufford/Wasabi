from flask import Flask, jsonify, Blueprint, request
from .db import get_db
from . import socketApi
import threading
import time

api_bp = Blueprint('api', __name__, url_prefix='/api')
@api_bp.route('/timerInit', methods=["GET", "POST"])
def sockTest():
    print('timer init called')
    for i in range(0,30):
        socketApi.emitter({'index':i})
        time.sleep(.25)
    return jsonify('sock event called')
