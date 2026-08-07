#!/bin/bash
. .venv/bin/activate
flask --app flaskApi run --host=0.0.0.0 --port=5000
