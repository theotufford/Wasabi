from flask import Flask
from .socketInstance import socketInstance
import threading
import os
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'WasabiData.sqlite'),
    )
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

    from .api import api_bp
    app.register_blueprint(api_bp)

    from . import socketApi 
    socketApi.register(socketInstance)

    socketInstance.init_app(app)

    return app
