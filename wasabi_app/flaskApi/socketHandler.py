from .socketInstance import socketInstance 
from .db import get_db
import json
from .api import getExperiment

def register(socketio):
    def saveExperiment(experiment):
        db = get_db()
        title = experiment.title
        experimentObject = getExperiment(title)
        if experiment.toDB:
            db.execute(
                    ''' 
                    INSERT INTO experiments (title, data) VALUES (?,?)
                    ''' , (title, experiment)
            )

    def reagentLibUpdate(data):
        db = get_db()
        data = json.loads(data)
        print("updating reagents")
        returnVal = "no update" # if not altered there was no update 
        for form in data['formArray']:
            reagent = form.get("reagent")
            if reagent:
                print(f"selected reagent: {reagent}")
                reagentRecord = db.execute(
                    '''
                    SELECT reagent FROM reagentLib WHERE reagent IS ? 
                    ''', (reagent,)).fetchone()
                if reagentRecord is None:
                    db.execute('INSERT INTO reagentLib (reagent) VALUES (?)', (reagent,))
                    db.commit()
                    returnVal = "updatedReagents"
        print(f"reagent return value:{returnVal}")
        return returnVal
    @socketio.on('dumpExperiment')
    def dump(data): # dumps all of the construction information for each form in the current experiment to the database
        db = get_db()
        session['autosave'] = data # convenient to auto-open the most recent experiment 
        experimentJson = json.dumps(data) # convert the real json dict obj into a string 
        resp = getExperiment(data)
        version = 0
        returnVal = reagentLibUpdate(data) # automatically attempt to log all the reagents, function has implicit duplicate protection
        if resp:
            if resp['data'] == experimentJson: # duplicate protection
                return jsonify('trying to save a perfect duplicate')
            version = resp['version']+1 # increment version if title exists
        db.execute(
            """
            INSERT INTO experiments (data, title, version) VALUES (?, ?, ?)
            """, 
            (experimentJson, data['title'], version)
        )
        db.commit()
        return jsonify("dumped!")

    @socketio.on('deleteExperiment')
    def deleteExperiment(data):
        db = get_db()
        db.execute( " DELETE FROM experiments WHERE title = ? AND version = ?", (data['title'],data['version']))
        db.commit()
        print(splitter(f'{data["title"]}_v{data["version"]} deleted'))
        return jsonify( f'{data["title"]}_v{data["version"]} deleted' )

    def run_experiment(data):

        db = get_db()
        experiment = getExperiment({"title": data})
        missing_contents  = [experiment[form]["contents"] for form in experimentif data[form]["contents"] not in pumpatlas]
        return jsonify( "run error" )
