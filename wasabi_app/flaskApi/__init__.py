from flask import Flask, session
from flask_session import Session
from flask_cors import CORS
import threading
import os

def create_app(test_config=None):
    app = Flask(__name__)
    app.debug = True
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    # import the database into the app

    from . import db
    db.init_app(app)

    # from . import serialComs
    # app.register_blueprint(serialComs.bp)

    from . import dataApi 
    app.register_blueprint(dataApi.bp)
    CORS(app, origins="http://localhost:5173", methods=["GET", "POST"]) # in final version the node server should start this one and pass its url
    Session(app)

    return app
