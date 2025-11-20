import sqlite3
import json

import click
from flask import current_app, g

DATABASE = "wbiDB.db"
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Allows dictionary-like access to rows
    return db


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
        if reagent == "not-configured":
            db.execute(
                """
                INSERT INTO pumpMap (pumpID, reagent) VALUES(?,?)
                """,
                (pump,reagent)
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
    with current_app.open_resource('../config.json') as j:
        config = j.read()
        count = json.loads(config)["machine"]["pumpCount"] 
        for id in range(1, count+1):
            name = "pump" + str(id)
            print(pumpUpdate({"pump":name, "reagent":"not-configured"}))



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
