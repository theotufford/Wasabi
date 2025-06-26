import json
from flask import (
    Blueprint, redirect, current_app, render_template, request, session, url_for, jsonify
)
from main.db import (get_db)
bp = Blueprint('runExperiment', __name__, url_prefix='/run')

def splitter(message):
    return f'\n-------------------\n{message}\n-------------------\n' 

alph = "abcdefghijklmnopqrstuvwxyz".split("")
invAlph = alph.reverse()


alph = list("abcdefghijklmnopqrstuvwxyz")
def byRows(data):
    datfrom = data['from']
    to = data['to']
    wells = {}
    for char in alph:
        wells[char] = []
    fromcol = int(datfrom[1:])
    tocol = int(to[1:])
    fromrow = alph.index(datfrom[0])
    torow = alph.index(to[0])
    outwells = {}
    for char in alph[fromrow:torow]:
        for wellNumber in [num for num in range(fromcol,tocol)]:
            wells[char].append(f"{char}{wellNumber}")
    for well in wells:
        if wells[well] == []:
            pass
        else:
            outwells[well] = wells[well]
    return outwells
def byCols(data):
    wells = {}
    datfrom = data['from']
    to = data['to']
    fromcol = int(datfrom[1:])
    tocol = int(to[1:])
    fromrow = alph.index(datfrom[0])
    torow = alph.index(to[0])
    for cord in range(1, tocol):
        wells[str(cord)] = []
    outwells = {}
    for wellNumber in [num for num in range(fromcol,tocol)]:
        for char in alph[fromrow:torow]:
            wells[str(wellNumber)].append(f"{char}{wellNumber}")
    for well in wells:
        if wells[well] == []:
            pass
        else:
            outwells[well] = wells[well]
    return outwells

@bp.route('/', methods=["POST"])
def translator(): # turns a loaded experiment data form into a map of the volumes in each well
    expdata = request.get_json()['experiment']
    wellmap = {} #end output dictionary of wells and and array of their contents
    for col in range(1, expdata['dimensions']['x']):
        for row in alph[:expdata['dimensions']['y']]:
            wellmap[f'{row}{col}'] = {}
    for key in expdata: #iterate through experiment data keys 
        form = expdata[key] 
        if not "form" in key:#make sure that key is a form and not the title or something else
            pass
        else:
            contents = form['pumpContents']
            if wellmap[list(wellmap.keys())[0]].get(contents) is None:
                for col in range(1, expdata['dimensions']['x']):
                    for row in alph[:expdata['dimensions']['y']]:
                        wellmap[f'{row}{col}'][contents] = 0
            if form['method'] == 'gradient':
                dir = form ['direction']
                match dir:
                    case 'up':
                        welldict = byRows(form)
                        for row in welldict.keys().reverse():
                            rowObj = welldict[row]
                            for well in rowObj:
                                wellmap[well][contents] += int(form['increment']*alph.index(row) + form['initialVolume']) 
                    case 'down':
                        welldict = byRows(form)
                        for row in welldict.keys():
                            rowObj = welldict[row]
                            for well in rowObj:
                                wellmap[well][contents] += int(form['increment']*alph.index(row) + form['initialVolume'])
                    case 'left':
                        welldict = byCols(form)
                        for col in welldict.keys().reverse():
                            colObj = welldict[col]
                            for well in colObj:
                                wellmap[well][contents] += int(form['increment']*int(col) + form['initialVolume']) 
                    case 'right':
                        welldict = byCols(form)
                        for col in welldict.keys():
                            colObj = welldict[col]
                            for well in colObj:
                                wellmap[well][contents] += int(form['increment']*int(col) + form['initialVolume']) 
            if form['method'] == "constant":
                welldict = byCols(form)
                for col in welldict.keys():
                    colObj = welldict[col]
                    for well in colObj:
                        wellmap[well][contents] += form['volume']
    optmap = {}
    for wellid in wellmap:
        well = wellmap[wellid]
        for analyte in well:
            analyteVolume = well[analyte]
            if analyteVolume != 0:
                if optmap.get(wellid) is None:
                    optmap[wellid] = {}
                optmap[wellid][analyte] = analyteVolume
            else:
                pass
    coordMap = getCoordMap("empty placeholder")
    outcode = ""
    for well in optmap:
        outcode += f"G0 X:{coordMap[well]['x']} Y:{coordMap[well]['y']} Z:0\n"
        pumptemp = 'P0'
        for analyte in optmap[well]:
            pumptemp += f" {analyte}:{optmap[well][analyte]}"
        outcode += f"{pumptemp}\n"
    return outcode
