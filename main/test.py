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
    'form_2': {'pumpContents': 'empty',
               'method': 'gradient',
               'direction': 'down',
               'initialVolume': 0,
               'increment': 1,
               'from': 'a1',
               'to': 'h12'},
    'title': 'awesome new experiment',
    'dimensions': {"x":12,"y":8}
}

alph = list("abcdefghijklmnopqrstuvwxyz")

def getCoordMap( fixtureMethod ): #placeholder for a function that would query the homing sequence data from the rtos
    wellmap = {}
    #spacing set to 5
    spacing = 5
    for rowdex in range(expdata['dimensions']["y"]):
        row = alph[rowdex]
        for coldex in range(expdata['dimensions']['x']):
            wellmap[f'{row}{(coldex + 1)}'] = {"x": coldex*spacing, "y": rowdex*spacing}
    return wellmap

def getPumpMap():
    #placeholder for database stuff to get the pump -> motor getCoordMap
    return {"empty": "p1"}


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
        for wellNumber in [num for num in range(fromcol,
                                                tocol)]:
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
    for cord in range(1,
                      tocol):
        wells[str(cord)] = []
    outwells = {}
    for wellNumber in [num for num in range(fromcol,
                                            tocol)]:
        for char in alph[fromrow:torow]:
            wells[str(wellNumber)].append(f"{char}{wellNumber}")
    for well in wells:
        if wells[well] == []:
            pass
        else:
            outwells[well] = wells[well]
    return outwells
def translator(expdata):
    wellmap = {} #end output dictionary of wells and and array of their contents
    for key in expdata: #iterate through experiment data keys 
        form = expdata[key] 
        if not "form" in key:#make sure that key is a form and not the title or something else
            pass
        else:
            contents = form['pumpContents']
            for col in range(1,
                             expdata['dimensions']['x']):
                for row in alph[:expdata['dimensions']['y']]:
                    wellmap[f'{row}{col}'] = {}
                    wellmap[f'{row}{col}'][contents] = 0
            if form['method'] == 'gradient':
                dir = form ['direction']
                match dir:
                    case 'up':
                        welldict = byRows(form)
                        for row in welldict.keys().reverse():
                            rowObj = welldict[row]
                            for well in rowObj:
                                wellmap[well][contents] += (form['increment']*alph.index(row) + form['initialVolume']) 
                    case 'down':
                        welldict = byRows(form)
                        for row in welldict.keys():
                            rowObj = welldict[row]
                            for well in rowObj:
                                wellmap[well][contents] += (form['increment']*alph.index(row) + form['initialVolume'])
                    case 'left':
                        welldict = byCols(form)
                        for col in welldict.keys().reverse():
                            colObj = welldict[col]
                            for well in colObj:
                                wellmap[well][contents] += (form['increment']*int(col) + form['initialVolume']) 
                    case 'right':
                        welldict = byCols(form)
                        for col in welldict.keys():
                            colObj = welldict[col]
                            for well in colObj:
                                wellmap[well][contents] += (form['increment']*int(col) + form['initialVolume']) 
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
            if optmap.get(wellid) is None and analyteVolume != 0:
                optmap[wellid] = well
            else:
                pass
    coordMap = getCoordMap("empty placeholder")
    outcode = ""
    pumpMap = getPumpMap()
    for well in optmap:
        outcode += f"W0 X{coordMap[well]['x']} Y{coordMap[well]['y']}\n"
        for analyte in optmap[well]:
            outcode += f"W0 {pumpMap[analyte]}{optmap[well][analyte]}\n"
    return outcode

print(translator(expdata))
