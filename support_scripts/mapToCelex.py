#takes tuple of (word, cmu pronunciation) and maps the vowels
#to their equivalent in the celex pronunciation
import argparse, os, re, sys
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
    mapping = filter(lambda a: a != ([],[]), vowMatch)
    
    if len(vowelInd_cmu)-1 != len(mapping): 
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
                                

def mapToCelex(word, pron):
    global celDict
    if not celDict:
        buildCelex()
    word = word.upper()
    assert word in celDict.keys(), '%r not in celex' % word 
    celPron = celDict[word]
    return mapVowels(pron,celPron[0])

















