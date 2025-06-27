import sqlite3
import json

import click
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def pumpUpdate(updatedict):
    pumpData = {}
    db = get_db()
    with current_app.open_resource('./static/resources/config.json') as f:
        try:
            pumpData = json.loads(db.execute('SELECT pumpData FROM pumpatlas').fetchone()[0])
        except Exception as e:
            print(e)
    pumpData[updatedict['name']] = updatedict['contents']
    print(json.dumps(pumpData))
    db.execute("DELETE FROM pumpatlas")
    db.execute(
        'INSERT INTO pumpatlas (pumpData) VALUES (?)',(json.dumps(pumpData), )
    )
    db.commit()


def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    with current_app.open_resource('./static/resources/config.json') as j:
        config = j.read()
        count = json.loads(config)["machineInfo"]["pumpCount"] 
        for id in range(1, count+1):
            name = "pump" + str(id)
            pumpUpdate({"name": name, "contents": "empty"})


@click.command('init-db')
def init_db_command():
    click.echo(
    """ \n WARNING: this will clear delete all of the data stored in the database and create new tables. 
       it should only be done if you are just building the application for the first time 
    \n if you are just updating the machine config you can use the \"configUpdate\" command 
    or if you just want to update the pumps or plate specifically from the config file you can use \"plateUpdate\" and \"pumpUpdate\" 
    \n """)
    choice = input("do you want to proceed? \n y/n:  ")
    if choice == "y":
        init_db()
        click.echo('tables cleared and database initialized.')
    else:
        click.echo("aborted")

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
