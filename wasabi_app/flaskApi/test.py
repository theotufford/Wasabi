expdata = {
    'form_0': {'pumpContents': 'empty',
               'method': 'constant',
               'volume': 20,
               'from': 'a1',
               'to': 'h4'},
    'form_1': {'pumpContents': 'empty',
               'method': 'gradient',
               'direction': 'right',
               'initialVolume': 0,
               'increment': 1,
               'from': 'a1',
               'to': 'h7'},
    'form_2': {'pumpContents': 'meeb',
               'method': 'gradient',
               'direction': 'down',
               'initialVolume': 0,
               'increment': 1,
               'from': 'a1',
               'to': 'h12'},
    'title': 'awesome new experiment',
    'dimensions': {"x":12,"y":8}
}

alph = list("abcdefghijklmnopqrstuvwxyz") #useful list for alphanumeric conversion

def getCoordMap( fixtureMethod ): #placeholder for a function that would query the homing sequence data from the rtos
    wellmap = {}
    #spacing set to 5
    spacing = 5
    for rowdex in range(expdata['dimensions']["y"]): #iterate through rows and columns assigning xy coords to them
        row = alph[rowdex]
        for coldex in range(expdata['dimensions']['x']):
            wellmap[f'{row}{(coldex + 1)}'] = {"x": coldex*spacing, "y": rowdex*spacing}
    return wellmap

def byRows(data): # to group wells into subdictionaries by alphabetical row
    wells = {}

    fromcol = int(data['from'][1:])
    tocol = int(data['to'][1:])
    fromrow = alph.index(data['from'][0])
    torow = alph.index(data['to'][0])

    for char in alph[fromrow:torow]:
        wells[char] = []
    for char in alph[fromrow:torow]:
        for column in range(fromcol, tocol):
            wells[char].append(f"{char}{column}")
    return wells

def byCols(data): # groups wells by numbered column
    wells = {} #init temp wells dict

    fromcol = int(data['from'][1:]) #get edges
    tocol = int(data['to'][1:])
    fromrow = alph.index(data['from'][0])
    torow = alph.index(data['to'][0])

    for column in range(fromcol, tocol): #  
        wells[str(column)] = [] 
        for char in alph[fromrow:torow]:
            wells[str(column)].append(f"{char}{column}") 
    return wells
def translator(expdata):
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
    pumpMap = getPumpMap()
    for well in optmap:
        outcode += f"G0 X:{coordMap[well]['x']} Y:{coordMap[well]['y']} Z:0\n"
#        pumptemp = ''
#        for analyte in optmap[well]:
#            pumptemp += f" {pumpMap[analyte]}:{optmap[well][analyte]}"
#        outcode += f"{pumptemp}\n"
    return outcode

print(translator(expdata))
