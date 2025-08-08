from flask import session, jsonify
from .socketInstance import socketInstance 
from .db import get_db
import json
from .api import getExperiment
if __name__ == "__main__":
    pass

def register(socketio):

    @socketio.on('updateReagents')
    def reagentLibUpdate(experiment):
        db = get_db()
        returnVal = "no update" # if not altered there was no update 
        for form in experiment.get('formArray') or []:
            reagent = form.get("reagent")
            if reagent is None: continue
            reagentRecord = db.execute(
            '''
            SELECT reagent 
            FROM reagentLib
            WHERE reagent IS ? 
            ''', (reagent,)).fetchone()
            if reagentRecord: continue 
            db.execute('INSERT INTO reagentLib (reagent) VALUES (?)', (reagent,))
            returnVal = "updatedReagents"
        db.commit()
        return returnVal

    @socketio.on('dumpExperimentToSession')
    def dump(experiment): # dumps all of the construction information for each form in the current experiment to the database
        print(f'dumping!\n{experiment}' )
        db = get_db()
        if not session.get('autosave'):
            session['autosave'] = experiment # convenient to auto-open the most recent experiment 
        return jsonify("dumped!")

    @socketio.on('saveExperiment')
    def saveExperiment(experiment):

        dump(experiment)
        experiment = session.get('autosave')
        db = get_db()

        title = experiment.get("title")
        version = 0
        experimentJson = json.dumps(experiment)
        currentExperimentOfTitle = getExperiment({"title":title})

        if currentExperimentOfTitle:
            reagentLibUpdate(experiment)
            version = currentExperimentOfTitle.get("version")
            if currentExperimentOfTitle.get('data') == experimentJson: # duplicate protection
                return jsonify('trying to save a perfect duplicate')

        db.execute(
            """
            INSERT INTO experiments (data, title, version) VALUES (?, ?, ?)
            """, 
            (experimentJson, title, version)
        )

        db.commit()

    @socketio.on('deleteExperiment')
    def deleteExperiment(experiment):
        db = get_db()
        db.execute( " DELETE FROM experiments WHERE title = ? AND version = ?", (experiment['title'],experiment['version']))
        print( f"deleted: {experiment['title']}")
        db.commit()

    def run_experiment(experimentTitle):
        db = get_db()
        if type(experimentTitle) is not str:
            raise ValueError("this function wants an experiment title, you gave it:\"{experimentTitle}\" ")
        missing_contents  = [experiment[form]["contents"] for form in experiment if data[form]["contents"] not in pumpatlas]
        if len(missing_contents) > 0:
            return jsonify( f"run error, missing contents: {missing_contents}" )
