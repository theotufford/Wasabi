from flask import Flask
from flask_cors import CORS  
import os
def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'WasabiData.sqlite'),
    )

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


    from . import api 
    app.register_blueprint(api.bp)

    os.system("npm run dev &")

    return app
