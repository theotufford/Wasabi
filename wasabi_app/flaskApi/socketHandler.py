from flask import Flask, jsonify, Blueprint, request, session
from .db import get_db
import json
from .dataApi import getExperiment
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

    @socketio.on('saveExperiment')
    def saveExperiment(experiment):
        if not experiment.get('formArray'):
            print('no data')
            return
        db = get_db()
        data = experiment['formArray']
        autoSave = experiment.get('autoSave')
        title = experiment.get("title")
        version = 0
        experimentJson = json.dumps(data)
        selected = getExperiment({"title":title})
        print(f"\n\nautosave = {autoSave}\n\n")
        reagentLibUpdate(experiment)
        if selected is not None:
            version = selected[ "version" ]
#            print(selected, experimentJson)
#            print(selected == experimentJson)
        elif autoSave: return jsonify({"data":"overactive autosave protection activated"})
        if selected is not None and selected['data'] == experimentJson: # duplicate protection
            print('trying to save duplicate, aborting')
            return jsonify('trying to save a perfect duplicate')

        if not autoSave:
            if selected is not None: version = version+1
            db.execute("""
                       INSERT INTO experiments (data, title, version) VALUES (?, ?, ?)
                       """, 
                      (experimentJson, title, version))
            db.commit()
            return jsonify({"version":version})
        db.execute("""
                   UPDATE experiments 
                   SET data = ?
                   WHERE (title = ? AND version = ?)
                   """, (experimentJson, title, version))
        db.commit()
