expdata = {
  'form_0': {
    'pumpContents': 'empty', 
    'method': 'constant', 
    'volume': '5', 
    'from': 'a1', 
    'to': 'h12'
  }, 
  'form_1': {
    'pumpContents': 'empty', 
    'method': 'gradient',
    'direction': 'right',
    'initialVolume': '0',
    'increment': '1',
    'from': 'a1',
    'to': 'h7'
  },
  'form_2': {
    'pumpContents': 'empty',
    'method': 'gradient',
    'direction': 'down',
    'initialVolume': '0',
    'increment': '1',
    'from': 'a1',
    'to': 'h12'}, 

  'title': 'awesome new experiment', 
  'dimensions': '{"x":"12","y":"8"}'
}

alph = list("abcdefghijklmnopqrstuvwxyz")


def byRows(datfrom, to):
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



wellmap = {} #end output dictionary of wells and and array of their contents
for key in expdata: #iterate through experiment data keys 
    form = expdata[key] 
    if not "form" in key:#make sure that key is a form and not the title or something else
        pass
    else:
        datfrom = form['from']
        to = form['to']
        print(byRows(datfrom, to))


