from . import db
from . import dataApi
from flask import Flask, session
from flask_session import Session
from flask_cors import CORS
import threading
import os


app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SESSION_TYPE"] = "filesystem"

# ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# import the database into the app
app.register_blueprint(dataApi.bp)

db.init_app(app)
CORS(app)



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
