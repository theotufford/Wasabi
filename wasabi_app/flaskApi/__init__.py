from . import db
import json
from .methods import methods
from . import dataApi
from . import controlApi
from flask import Flask, session
from flask_session import Session
from flask_cors import CORS
import os
# from .machine import kinematics
# from .import machine as mach


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
db.init_app(app)

# with app.app_context():
#     machine = mach.Machine(
#         "./public/machine_config.json", methods)

# methods.output_methods_outline()
# ctlAPI = controlApi.machine_aware_bp_factory(machine)

# app.register_blueprint(ctlAPI, url_prefix="/control")
