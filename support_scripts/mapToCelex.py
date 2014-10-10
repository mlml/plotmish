#takes tuple of (word, cmu pronunciation) and maps the vowels
#to their equivalent in the celex pronunciation
#If run with saveFile argument it saves word to word pronuciations
#in a text file for quicker retrieval later on  
import os, re, sys,  time
from os import path
'''
cmuVowels = ['IY', 'IA', 'N~', 'L~', 'NG~', 'AA', 'AE', 'EH', 'AH',
			 'EA', 'AO', 'IH', 'EY', 'AW', 'AY', 'M~', 'ER', 'UW', 'UH', 'OY', 'OW', 'UA']
celexVowels = ['#', '$', '1', '0', '3', '2', '5', '4', '7', '6', '9',
			 '8', '@', 'C', 'E', 'F', 'I', 'H', 'Q', 'P', 'U', 'V', 'c', 'i', 'q', 'u', '{', '~']
'''
translate = {'': [''], 'D': ['DH','TH'], 'J': ['CH'], 'N': ['NG'], 'S': ['SH'], 'R': ['R'], 
			'T': ['TH','DH'], 'Z': ['ZH'], '_': ['JH'], 'b': ['B'], 'd': ['D'], 'g': ['G'],
			 'f': ['F'], 'h': ['HH'], 'k': ['K'], 'j': ['Y'], 'm': ['M'], 'l': ['L'],
			  'n': ['N'], 'p': ['P'], 's': ['S'], 'r': ['R'], 't': ['T'], 'w': ['W'], 
			  'v': ['V'], 'x': ['X'], 'z': ['Z']}
cmuCons = []
for c in translate.values():
    cmuCons += c

celexPath = path.join(os.getcwd(),'celex.cd')

saveDict = {}

celDict = {}

def buildCelex():   
    global celDict, celexPath
    cel = open(celexPath,'rb').readlines()
    celDict = {}
    for word in cel:
        word = word.split('\\')
        upWord = word[1].upper()
        if upWord in celDict:
            celDict[upWord] = celDict[upWord] + [[p for p in word[6] if p not in  ['-',"'",'"']]]
        else:
            celDict[upWord] = [[p for p in word[6] if p not in  ['-',"'",'"']]]
    assert celDict
    return celDict

def changeCelexPath(path, rebuildDict = True):
    global celexPath
    assert os.path.isfile(path)
    celexPath = path
    if rebuildDict:
        buildCelex()

def weight(cmu,cel):
    if cmu in cmuCons and cel in translate.keys():
        if cmu in translate[cel]: 
            return 'match'
        elif cel == 'R':
            return 'sandhi'
        else: return 'nomatch'
    else: 
        return 'vowel'

def dealWithHiatus(match):
    newMatches = []
    if len(match[0]) == len(match[1]):
        if len([m for m in match[0] if m not in cmuCons]) == len(match[0]):
            if len([m for m in match[1] if m not in translate.keys()]) == len(match[1]):
                for m in range(len(match[0])):
                    newMatches += [(match[0][m],match[1][m])]
    if newMatches:
        return newMatches
    return [match]
deads = {}
def mapVowels(cmu,cel):
    cmu += ['']
    cel += ['']
    vowMatch = []
    prev = (0,0)
    for i,cm in enumerate(cmu):
        if i<prev[0]: continue
        for j,ce in enumerate(cel):
            if j<prev[1]: continue
            match = weight(cm,ce)
            if match == 'match':        
                vowMatch += dealWithHiatus((cmu[prev[0]:i],cel[prev[1]:j]))
                prev = (i+1,j+1)
                break
            elif match == 'nomatch': 
                break
    vowelInd_cmu = [-1]+[cmu.index(v) for v in cmu if v not in cmuCons] 
    vowelInd_cel = [-1]+[cel.index(v) for v in cel if v not in translate.keys()]
    mapping = [m for m in vowMatch if m[0]]
    mapping = filter(lambda a: a != ([],[]), vowMatch)
    
    if len(vowelInd_cmu)-1 != len(mapping) and len(vowelInd_cel)-1 != len(mapping):
        deads[mapping] = ''
        newCmu, newCel = list(cmu),list(cel)
        shorter = min(len(vowelInd_cel), len(vowelInd_cmu))
        for s in range(1,shorter):
            if vowelInd_cmu[s]-vowelInd_cmu[s-1] != vowelInd_cel[s]-vowelInd_cel[s-1]:
                for d in range(vowelInd_cmu[s-1]+1,vowelInd_cmu[s]):
                    newCmu.remove(cmu[d])
                for d in range(vowelInd_cel[s-1]+1,vowelInd_cel[s]):
                    newCel.remove(cel[d])
        return mapVowels(newCmu[:-1],newCel[:-1])
    

    return mapping                    
                                

def readSaved(saveFile):
    global saveDict 
    assert os.path.isfile(saveFile), 'file does not exist %r' %saveFile
    sF = open(saveFile, 'rb')
    saveDict = {(s[0],s[1]) : [tuple(w.split() for w in y.split('/')) if ' ' in y else tuple(y.split('/')) for y in s[2].split('//')] for s in [x.strip('\n').split('  ') for x in sF.readlines()]}
    sF.close()
    return saveDict

def writeSaved(saveFile):
    saveF = open(saveFile, 'a')
    for w,p in saveDict.items():
        for e in range(len(p)):
            if isinstance(p[e][0],list):
                p[e] = '/'.join([' '.join(i) for i in p[e]])
            else:
                p[e] = '/'.join(p[e])
        p = '//'.join(p)
        saveF.write(w[0]+'  '+str(w[1])+'  '+p+'\n')
    saveF.close()

def newSaveFile(saveFile):
    saveF = open(saveFile, 'wb')
    saveF.close()

def mapToCelex(word, pron, makeSave = False):
    global celDict, saveDict
    if not celDict:
        buildCelex()
    word = word.upper()
    if word not in celDict:
        if makeSave: 
            saveDict[(word,''.join(pron))] = ''
        return ''
    celPron = celDict[word]
    mapped = mapVowels(pron,celPron[0])
    if makeSave: 
        saveDict[(word,''.join(pron))] = mapped 
    return mapped

















