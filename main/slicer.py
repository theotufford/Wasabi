def splitter(message):
    return f'\n-------------------\n{message}\n-------------------\n' 
alph = "a b c d e f g h i j k l m n o p q r s t u v w x y z".split(" ")
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


def translate(expdata): # turns a loaded experiment data form into a map of the volumes in each well
    wellmap = {} #end output dictionary of wells and and array of their contents
    dimensions = {
            'x':int(expdata['dimensions']['x']),
            'y':int(expdata['dimensions']['y'])
            }
    for col in range(1, dimensions['x']):
        for row in alph[:dimensions['y']]:
            wellmap[f'{row}{col}'] = {}
    for key in expdata: #iterate through experiment data keys 
        form = expdata[key] 
        if not "form" in key:#make sure that key is a form and not the title or something else
            pass
        else:
            reagent = form['reagent']
            if wellmap[list(wellmap.keys())[0]].get(reagent) is None:
                for col in range(1, dimensions['x']):
                    for row in alph[:dimensions['y']]:
                        wellmap[f'{row}{col}'][reagent] = 0
            if form['method'] == 'gradient':
                dir = form ['direction']
                match dir:
                    case 'up':
                        welldict = byRows(form)
                        for row in welldict.keys().reverse():
                            rowObj = welldict[row]
                            for well in rowObj:
                                wellmap[well][reagent] += int(form['increment']*alph.index(row) + form['initialVolume']) 
                    case 'down':
                        welldict = byRows(form)
                        for row in welldict.keys():
                            rowObj = welldict[row]
                            for well in rowObj:
                                wellmap[well][reagent] += int(form['increment']*alph.index(row) + form['initialVolume'])
                    case 'left':
                        welldict = byCols(form)
                        for col in welldict.keys().reverse():
                            colObj = welldict[col]
                            for well in colObj:
                                wellmap[well][reagent] += int(form['increment']*int(col) + form['initialVolume']) 
                    case 'right':
                        welldict = byCols(form)
                        for col in welldict.keys():
                            colObj = welldict[col]
                            for well in colObj:
                                wellmap[well][reagent] += int(form['increment']*int(col) + form['initialVolume']) 
            if form['method'] == "constant":
                welldict = byCols(form)
                for col in welldict.keys():
                    colObj = welldict[col]
                    for well in colObj:
                        wellmap[well][reagent] += form['volume']
    print('done with wellmap \n\n\n')
    print(wellmap,'\n\n\n')
    optmap = {}
    for wellid in wellmap:
        well = wellmap[wellid]
        for reagent in well:
            reagentVolume = well[reagent]
            if reagentVolume != 0:
                if optmap.get(wellid) is None:
                    optmap[wellid] = {}
                optmap[wellid][reagent] = reagentVolume
            else:
                pass
    #spacing set to 5
    coordMap = {}
    spacing = 5
    for rowdex in range(dimensions["y"]): #iterate through rows and columns assigning xy coords to them
        row = alph[rowdex]
        for coldex in range(dimensions['x']):
            coordMap[f'{row}{(coldex + 1)}'] = {"x": coldex*spacing, "y": rowdex*spacing}
    outcode = ""
    for well in optmap:
        outcode += f"G0 X:{coordMap[well]['x']} Y:{coordMap[well]['y']} Z:0\n"
        pumptemp = 'P0'
        for key, value in optmap[well].items():
            pumptemp += f" {key}:{value}"
        outcode += f"{pumptemp}\n"

    print(outcode)
    return outcode
