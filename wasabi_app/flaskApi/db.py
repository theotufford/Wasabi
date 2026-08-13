import sqlite3
import json

import click
from flask import current_app, g

DATABASE = "wbiDB.db"

def get_db() -> sqlite3.Connection:
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Allows dictionary-like access to rows
    return db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def pumpUpdate(id=None, reagent=None):
    db = get_db()
    if id is not None and reagent is not None:
        if reagent == "not-configured":
            db.execute(
                """
                INSERT INTO pumpMap (pumpID, reagent) VALUES(?,?)
                """,
                (id, reagent)
            )
            db.commit()
            return f"pump {id} created"
        else:
            db.execute(
                """
                UPDATE pumpMap
                SET reagent = ?
                WHERE pumpID = ?
                """,
                (reagent, id)
            )
            db.commit()
            print(f"pump updated: {id}:{reagent}")
            return
    else:
        print(f"value fail, {id=} {reagent=}")
        return


def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    with current_app.open_resource('../public/machine_config.json') as j:
        config = j.read()
        pumps = json.loads(config)["machine"]["motors"]["pumps"]
        print(pumps)
        count = len(pumps)
        print(count)
        for id in range(0, count):
            print(f"pump to create: {id}  ")
            pumpUpdate(id=id, reagent="not-configured")
        db.execute("""
                   INSERT INTO experiments (title, version)
                   VALUES (?,?)
                   """, ("autoSave", 0))
        db.commit()
    close_db()


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
