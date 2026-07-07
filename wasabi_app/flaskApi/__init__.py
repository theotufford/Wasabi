from . import db
from .machine import machine_state as mach
from .machine import serialcoms as ser
from . import dataApi
from . import controlApi
from flask import Flask, session
from flask_session import Session
from flask_cors import CORS
import threading
import os


app = Flask(__name__)
CORS(app, origins="*")
app.config["DEBUG"] = True
app.config["SESSION_TYPE"] = "filesystem"

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

app.register_blueprint(dataApi.bp)

# import the database into the app

coms = ser.ComsChannel()
machine_state = mach.Machine(coms, "./flaskApi/machine/machine_config.json")

ctlAPI = controlApi.machine_aware_bp_factory(machine_state)


app.register_blueprint(ctlAPI, url_prefix="/control")

db.init_app(app)
if "__name__" == "__main__":
    app.run(host='0.0.0.0', port=5000)
