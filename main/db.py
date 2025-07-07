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


def pumpUpdate(addition):
    db = get_db()
    pump = None
    reagent = None
    try:
        pump = addition.get("pump")
        reagent = addition.get("reagent")
    except Error as e:
        return(e)
    if pump and reagent:
        if reagent == "new-empty":
            db.execute(
                """
                INSERT INTO pumpMap (pumpID) VALUES(?)
                """,
                (pump,)
            )
            db.commit()
            return f"{pump} created"
        else:
            db.execute(
                """
                UPDATE pumpMap
                SET reagent = ?
                WHERE pumpID = ?
                """, 
                (reagent, pump) 
            )
            db.commit()
            return f"pumps updated: {pump}:{reagent}"
    else:
        return f"value fail, {pump=} {reagent=}"
def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    with current_app.open_resource('./static/resources/config.json') as j:
        config = j.read()
        count = json.loads(config)["machineInfo"]["pumpCount"] 
        for id in range(1, count+1):
            name = "pump" + str(id)
            print(pumpUpdate({"pump":name, "reagent":"new-empty"}))



@click.command('init-db')
def init_db_command():
    click.echo(
    """ \n WARNING: this will clear delete all of the data stored in the database and create new tables. 
       it should only be done if you are just building the application for the first time 
    \n if you are just updating the machine config you can use the \"configUpdate\" command 
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
