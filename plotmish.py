# -*- coding: utf-8 -*-
'''
Python alternative to plotnik 

-Takes as input a .plt file (output of the FAAV-extract program) and a corresponding .wav file
-Displays all vowels according to F1 and F2
-Subsets of vowels can be displayed individually
-When play button is off; scroll over the vowel to display the relevant info about that vowel
-When play button is on: scrolling over will also play the vowel sound
-Hit enter while play is on to display other possible measurements of the vowel whose info is
currently being displayed (measurements are based on F1 and F2 values at 20%,35%,50%,65%,80%, 
of the vowel's duration)
-choose a new measurement from the options displayed (black buttons) or keep the original 
measurement (white button)
-all remeasurements are written to the log.txt file (or other file, specified with the -o flag)

requires SOX, Praat and pygame to run

If using the txtRead option then add the line:
    candidates = T 
in the config.txt file when running FAVE-extract
This will allow for the option to remeasure a vowel based on the number of formants

sox.sourceforge.net/
www.pygame.org/ 

by: Misha Schwartz
'''

import pygame, sys, argparse, os, re, csv, math, copy
from glob import glob
sys.path.append('support_scripts')
import pygbutton, inputbox, mapToCelex
from pygame.locals import *
from subprocess import call, Popen
import numpy as np

global vowByCode, vowByClass, codes, classes, maxF1,maxF2, allvowels, inputType, files, pitchFiles, myfont, DISPLAYSURFACE

#set window sizes and frames per second
FPS = 10
WINDOWWIDTH = 820
PLOTWIDTH = 700
WINDOWHEIGHT = 850
PLOTBOTTOM = 600
NOTPLOTRECTS = (pygame.Rect(PLOTWIDTH,0,WINDOWWIDTH - PLOTWIDTH, PLOTBOTTOM),
                pygame.Rect(0,PLOTBOTTOM,WINDOWWIDTH,WINDOWHEIGHT - PLOTBOTTOM))


#set default black and white colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# parse in arguments from the command line
parser = argparse.ArgumentParser(description = 'Make blank textgrids for transcription of DR uncut clips')
parser.add_argument('vowels', metavar = 'vowel info', help = '.plt file or formant.txt file or folder containing many')
parser.add_argument('wav', metavar = 'wav file', help = '.wav file or folder containing many')
parser.add_argument('-k', metavar = 'keyword', default = '*', help = 'keyword for selecting files in a directory, default is all files in the directory')
parser.add_argument('-o', metavar = 'output file', default = 'log', help = 'change folder to write log files to, default is plotmish/logs')
parser.add_argument('-a',  action = 'store_true', help = 'append to older log file instead of writing over it')
parser.add_argument('-p', metavar = 'Praat', default = '/Applications/Praat.app', help = 'change path to Praat application, default is /Applications/Praat.app')
parser.add_argument('-f0', metavar = 'pitch tracks', default = '', help = 'folder containing pre-generated pitch tracks for each sound file')
args = parser.parse_args()

# dictionary of all vowel codes and corresponding colours
# identical colours for vowels who corespond to the same ARPABET vowel type
colours = {`1` : Color("saddlebrown"),
     `2` : Color("tomato"),
     `3` : Color("thistle"),
     `5` : Color("aquamarine"),
     `6` : Color("lawngreen"),
     `7` : Color("hotpink"),
     `11` : Color("orange2"),
     `21` : Color("magenta4"),
     `41` : Color("mediumseagreen"),
     `61` : Color("royalblue"),
     `42` : Color("olivedrab"),
     `62` : Color("deepskyblue"),
     `72` : Color("grey47"),
     `53` : Color("red"),
     `94` : Color("lawngreen"),
     `82` : Color("firebrick4"),
     '8'  : Color("lightsalmon"),
     '12' : Color("orange2"),
     '14' : Color("orange2"),
     '22' : Color("magenta4"),
     '24' : Color("magenta4"),
     '33' : Color("thistle"),
     '39' : Color("thistle"),
     '43' : Color("yellow"),
     '44' : Color("yellow"),
     '47' : Color("mediumseagreen"),
     '54' : Color("red"),
     '63' : Color("deepskyblue"),
     '64' : Color("deepskyblue"),
     '73' : Color("grey47"),
     '74' : Color("grey47")} 
# dictionary of all vowel codes and names 
codes = {`1` : "i",
         `2` : "e",
         `3` : "ae",
         `5` : "o",
         `6` : "uh",
         `7` : "u",
         `8` : "*",
         `11` : "iy",
         `12` : "iyF",
         `21` : "ey",
         `22` : "eyF",
         `41` : "ay",
         `47` : "ay0",
         `61` : "oy",
         `42` : "aw",
         `62` : "ow",
         `63` : "owF",
         `72` : "uw",
         `73` : "Tuw",
         `82` : "iw",
         `33` : "aeh",
         `39` : "aeBR",
         `43` : "ah",
         `53` : "oh",
         `14` : "iyr",
         `24` : "eyr",
         `44` : "ahr",
         `54` : "ohr",
         `64` : "owr",
         `74` : "uwr",
         `94` : "*hr"}

# vowel codes by ARPABET vowel names
arpCodes ={`11` : "IY",                `72` : "UW",
        `1` : "IH",                 `7` : "UH",
        `21` : "EY",                `62` : "OW",
        `2` : "EH",     `6` : "AH", `53` : "AO",
        `3` : "AE",                  `5` : "AA",
                    
     
            `41` : "AY",    `94` : "ER",
            `61` : "OY", 
            `42` : "AW",
            `82` : "IW"}
revArpCodes =   {'AA': '5',
                 'AE': '3',
                 'AH': '6',
                 'AO': '53',
                 'AW': '42',
                 'AY': '41',
                 'EH': '2',
                 'ER': '94',
                 'EY': '21',
                 'IH': '1',
                 'IW': '82',
                 'IY': '11',
                 'OW': '62',
                 'OY': '61',
                 'UH': '7',
                 'UW': '72'}
# write to new log file or append to old one
def writeLogs(allLogs, append = False):
    for f,writeThis in allLogs.items():
        if not writeThis: continue
        header = True if not os.path.isfile(os.path.join(args.o,os.path.basename(f).replace('.wav','-corrLog.csv'))) else False
        if args.a or append:
            log = csv.writer(open(os.path.join(args.o,os.path.basename(f).replace('.wav','-corrLog.csv')),'a'))
            if header: log.writerow(['vowel','word','oldTime','newTime','duration (ms)','stress','maxForms','oldF1','newf1','oldF2','newF2'])
        else:
            log = csv.writer(open(os.path.join(args.o,os.path.basename(f).replace('.wav','-corrLog.csv')),'wb'))
            log.writerow(['vowel','word','oldTime','newTime','duration (ms)','stress','maxForms','oldF1','newf1','oldF2','newF2'])

        # write header to log file
        for k,w in writeThis.items():
            log.writerow(w)

# vowel classes TO DO: double check these, I think there are some vowels in the wrong classes 
# classes defined from http://fave.ling.upenn.edu/downloads/Plotnik%20cheat%20sheet.pdf
# some classes also defined by me where not defined in the above pdf

classes = { 'Short' : [str(i) for i in [1,2,3,5,6,7,8]], 
            'Long' : [str(i) for i in [12,22,63,11,21,31,41,61,82,42,62,72,53,13,23,33,43]],
            'Front' : [str(i) for i in [1,2,3,11,21,31,82,13,23,33,12,22,14,24,39,82]],
            'Back' : [str(i) for i in [5,7,61,62,72,53,63,62]],
            'High' : [str(i) for i in [1,7,11,72,82,13,12,73,14,74]],
            'Low' : [str(i) for i in [3,41,42,8,31,41,42,33,43,47,41,44,39,5]],
            'Mid' : [str(i) for i in [6,94,2,21,61,62,8,5,22,24,64,5]],
            'Centr.' : [str(i) for i in [42,94,41,6,8,47,44,43]],
            'Diph' : [str(i) for i in [41,42,61,82,47]],
            'Rhot' : [str(i) for i in [14,24,44,54,74,94]]}

if args.f0: pitchFiles = glob(os.path.join(args.f0,'*.Pitch'))


def getFiles():
    global files, inputType
    files = []
    if os.path.isdir(args.wav) and os.path.isdir(args.vowels):
        wFiles = glob(os.path.join(args.wav,'*'+args.k+'*.wav'))
        vFiles = glob(os.path.join(args.vowels,'*'+args.k+'*'))
        vFiles = [v for v in vFiles if '.plt' in v or 'formant.txt' in v]
        for w in wFiles:
            for v in vFiles:
                if os.path.basename(w.replace('.wav','')) in os.path.basename(v):
                    files += [(w,v)]
                    
    elif os.path.isdir(args.wav):
        wFiles = glob(os.path.join(args.wav,'*'+args.k+'*.wav'))
        for w in wFiles:
            if os.path.basename(w.replace('.wav','')) in os.path.basename(args.vowels):
                files += [(w,args.vowels)]
    elif os.path.isdir(args.vowels):
        vFiles = glob(os.path.join(args.vowels,'*'+args.k+'*'))
        for v in vFiles:
            if os.path.basename(args.wav.replace('.wav','')) in os.path.basename(v):
                files += [(args.wav,v)]
    else:
        files += [(args.wav,args.vowels)]
    both = ''
    for f in files:
        f = f[1]
        if '.plt' in f: both += 'plt'
        if 'formant.txt' in f: both += 'txt'
    if 'txt' in both and 'plt' in both:
        response = ''
        while response not in ['p','t']:
            response = raw_input('Found both text files and plotnik files \nWhich file type do you want to use? \n(p)lotnik or (t)ext:  ') 
        response = '.plt' if response == 'p' else 'formant.txt'
        files = [f for f in files if response in f[1]]
    assert files, 'ERROR: no files found'
    inputType = 'plt' if '.plt' in files[0][1] else 'txt'


def calculateVowelLocation(f):
    # calculates the location to display the vowel based on tuple of (F1,F2)
    x = (((maxF2-float(f[1])))/(maxF2-minF2))*(PLOTWIDTH-100)+ 50
    y = ((float(f[0]) - minF1)/(maxF1-minF1))*(PLOTBOTTOM-100)+ 50
    return (x,y)

def makeVowels():
    # makes buttons for the initial vowels and assigns colours
    # returns a dictionary of {(F1,F2):[button,(F1,F2),(vowelCode,stress,duration,word,timestamp,(extra formants))]}
    vowButtons = {}
    for f,v in allvowels.items():
        x,y = calculateVowelLocation(f)
        buttonRect = pygame.Rect(x,y, 8, 8)
        buttonRect.center = (x,y)
        button = pygbutton.PygButton(buttonRect,'►'.decode('utf8'),border = False)
        button.bgcolor = colours[v[0]]
        button.fgcolor = colours[v[0]]
        if v[0] not in vowButtons:
            vowButtons.update({v[0]:[(button,f,v)]})
        else:
            vowButtons[v[0]] += [(button,f,v)] 
    return vowButtons

def getCelexVowel(word,cmu,vIndex):
    allIndexes = [i for i,c in enumerate(cmu) if c[:-1] in revArpCodes.keys()]
    vIndex = allIndexes.index(vIndex)
    try:
        celVowel = mapToCelex.mapToCelex(word,cmu)[vIndex][1][0]
    except: 
        celVowel = 'NA'
    return celVowel

oldPitchFile = None
oldPitchFrame = 0

def getPitch(pitchList, timestamp, thisPitch):
    global oldPitchFile, oldPitchFrame
    dx = None
    x1 = None
    ceiling  = None
    for p in pitchList:
        pvar = p.split('=')
        if 'dx' in pvar[0]: dx = float(pvar[1].strip())
        if 'x1' in pvar[0]: x1 = float(pvar[1].strip())
        if 'ceiling' in pvar[0]: 
            ceiling = float(pvar[1].strip())
            break
    frame = '['+str(int(((float(timestamp)-x1)/dx)))+']'
    foundFrame = False
    pitch = 'Not Found'
    if oldPitchFile != thisPitch:
        oldPitchFrame = 0
    startHere = oldPitchFrame 
    for i,p in enumerate(pitchList[startHere:]):
        if 'frame' in p and frame in p: foundFrame = True
        if foundFrame and 'candidate [1]' in p:
            pitchNum = float(pitchList[i+startHere+1].split('=')[1].strip())
            if pitchNum != 0 and pitchNum < ceiling:
                pitch = str(int(pitchNum))
            oldPitchFile = thisPitch
            oldPitchFrame = i+oldPitchFrame
            return pitch
                 

def getVowelsTxt():
    # reads all the vowels from the formant.txt file
    global allvowels, maxF1,maxF2,minF1,minF2,myfont, DISPLAYSURFACE
    allvowels = {}
    for f in files:
        loadingMessage(DISPLAYSURFACE, myfont, ['Loading Vowels', os.path.basename(f[0]).replace('.wav','')])
        if args.f0: 
            thisPitch = [p for p in pitchFiles if os.path.basename(p).replace('.Pitch','') in os.path.basename(f[0])][0]
            pitchList = [p.replace('\n','').strip() for p in open(thisPitch,'rU').readlines()]
        vowelF = open(f[1],'r')
        vowels = vowelF.readlines()[3:]
        for i,v in enumerate(vowels):
            v = v.split('\t')
            # get other formant measurements from various points in the vowel duration  
            # (F1@20%, F2@20%, F1@35%, F2@35%, F1@50%, F2@50%, F1@65%, F2@65%, F1@80%, F2@80%)
            extraForms = tuple(v[21:31])
            x4m = []
            for i in range(0,len(extraForms),2):
                try: x4m += [(float(extraForms[i]),float(extraForms[i+1]))]
                except: continue 
            moreForms = [re.sub('[\[\]]','',m).split(',') for m in v[36].split('],[')]
            numForms = []
            for m in moreForms:
                try:
                    temp = [tuple([float(n.strip()) for n in m[:2]])]
                except: 
                    assert False, 'ERROR:\tthe formant.txt files do not contain extra formant measurement info\n\t\t\tmake sure the config.txt file in FAVE-extract has the line:\n\t\t\tcandidates=T\n\t\t\tand then re-extract the formant values'
                if len(temp[0]) != 2:
                    continue
                numForms += temp
            cmuPron = [p.strip() for p in re.sub('[\[\]\']','',v[33]).split(',')]
            pPhone = v[31]
            fPhone = v[32]
            word = v[2]
            vIndex = int(v[34])
            celVowel = getCelexVowel(word,cmuPron,vIndex)
            timestamp = v[9]
            if args.f0: pitch = getPitch(pitchList,timestamp, thisPitch) 
            formNums = v[35]
            # (F1, F2) = (vowelCode,stress,duration,word,timestamp,(extra formants))
            vowelCode = revArpCodes[v[0].strip()]
            stress = v[1]
            duration = str(int(float(v[12])*1000))
            info = [vowelCode,stress,duration,word,timestamp,x4m,numForms,celVowel,pPhone,fPhone,formNums]
            if args.f0: info += [pitch]
            allvowels[(float(v[3]),float(v[4]),f[0])] = tuple(info)

        #makeVowelClasses()
        # gets the max and min F1 and F2 
    maxF1 = max([float(f[0]) for f in allvowels.keys()])
    minF1 = min([float(f[0]) for f in allvowels.keys()])
    maxF2 = max([float(f[1]) for f in allvowels.keys()])
    minF2 = min([float(f[1]) for f in allvowels.keys()])

def getVowels():
    # reads all the vowels from the .plt file 
    global allvowels, maxF1,maxF2,minF1,minF2, myfont, DISPLAYSURFACE
    allvowels = {}
    for f in files:
        loadingMessage(DISPLAYSURFACE, myfont, ['Loading Vowels', os.path.basename(f[0]).replace('.wav','')])
        if args.f0: 
            thisPitch = [p for p in pitchFiles if os.path.basename(p).replace('.Pitch','') in os.path.basename(f[0])][0]
            pitchList = [p.replace('\n','').strip() for p in open(thisPitch,'rU').readlines()]
        vowelF = open(f[1],'r')
        vowelList = vowelF.readlines()[0].split('\r\r')[0].split('\r')
        #vowels = [re.sub('<.*>','',v) for v in vowels][2:]
        vowels = [v.split('<')[0] for v in vowelList][2:]
        extraFormants = [re.findall('<.*>',v) for v in vowelList][2:]
        for i,v in enumerate(vowels):
            # get other formant measurements from various points in the vowel duration  
            # (F1@20%, F2@20%, F1@35%, F2@35%, F1@50%, F2@50%, F1@65%, F2@65%, F1@80%, F2@80%)
            extraForms = re.sub('[<>]','',extraFormants[i][0])
            extraForms = extraForms.split(',')
            x4m = []
            for i in range(0,len(extraForms),2):
                try: x4m += [(float(extraForms[i]),float(extraForms[i+1]))]
                except: continue 
            v = v.split(',')
            word = v[5].split()[0]
            formNums = v[5].split()[1].replace('/','')
            timestamp = v[5].split()[-1]
            if args.f0: pitch = getPitch(pitchList,timestamp, thisPitch)
            # (F1, F2) = (vowelCode,stress,duration,word,timestamp,(extra formants))
            vowelCode = v[3].split('.')[0]
            stress = v[4].split('.')[0]
            stress = '0' if stress == '3' else stress
            duration = v[4].split('.')[1]
            info = [vowelCode,stress,duration,word,timestamp,x4m,formNums]
            if args.f0: info += [pitch]
            allvowels[(float(v[0]),float(v[1]),f[0])] = tuple(info)
        
        makeVowelClasses()
        # gets the max and min F1 and F2 
    maxF1 = max([float(f[0]) for f in allvowels.keys()])
    minF1 = min([float(f[0]) for f in allvowels.keys()])
    maxF2 = max([float(f[1]) for f in allvowels.keys()])
    minF2 = min([float(f[1]) for f in allvowels.keys()])

def makeVowelClasses():
    # sorts vowesl in allvowels in to classes
    vowByCode = {k:{} for k in codes.keys()}
    vowByClass = {k:{} for k in classes.keys()}
    for f,v in allvowels.items():
        vowByCode[v[0]].update({f:v})
        for names, nums in classes.items():
            if v[0] in nums:
                vowByClass[names].update({f:v})

def confidenceEllipse(xyPoints,sdev,screen):
    # make a confidence ellipse of the points currently plotted on the scree
    # adapted from Jaime at: 
    #stackoverflow.com/questions/20126061/creating-a-confidence-ellipses-in-a-sccatterplot-using-matplotlib
    x = [calculateVowelLocation(xy)[0] for xy in xyPoints]
    y = [calculateVowelLocation(xy)[1] for xy in xyPoints]
    angleAdjust = False if np.mean([p[1] for p in sorted(xyPoints)[:int(len(xyPoints)/2.0)]]) < np.mean([p[1] for p in sorted(xyPoints)[int(len(xyPoints)/2.0):]]) else True
    mean = (np.mean(x),np.mean(y))
    cov = np.cov(x, y)
    lambda_, v = np.linalg.eig(cov)
    lambda_ = np.sqrt(lambda_)
    angle = np.rad2deg(np.arccos(v[0, 0]))
    if angleAdjust: angle = 180-angle
    width=lambda_[0]*sdev*2
    height=lambda_[1]*sdev*2
    screen.fill(WHITE)
    ellipDim = pygame.Rect(0,0,width,height)
    ellipDim.center = (WINDOWWIDTH/2.0,WINDOWHEIGHT/2.0)
    pygame.draw.ellipse(screen,BLACK,ellipDim,2)
    rot_img = pygame.transform.rotate(screen, angle)
    img_rect = rot_img.get_rect()
    img_rect.center = mean
    return (rot_img, img_rect)


def makeButtons():
    global inputType
    # make permanent buttons (on the bottom of the screen)
    vowButtons = []
    classButtons = []
    onOffButtons = []
    removeButtons = []
    celexButtons = []
    # front
    for i,c in enumerate(['11','1','21','2','3']):
        name  = codes[c]
        if inputType == 'txt': name = arpCodes[c]
        button = pygbutton.PygButton((20, 640+(i*35), 30, 30), name)
        button.bgcolor = colours[c]
        vowButtons.append(button)
    # central
    centralbuttons = ['6'] if inputType == 'txt' else ['6','43']
    for i,c in enumerate(centralbuttons):
        name = codes[c]
        if inputType == 'txt': name = arpCodes[c]
        button = pygbutton.PygButton((60, 710+(i*35), 30, 30), name)
        button.bgcolor = colours[c]
        vowButtons.append(button)
    # back
    for i,c in enumerate(['72','7','62','53','5']):
        name  = codes[c]
        if inputType == 'txt': name = arpCodes[c]
        button = pygbutton.PygButton((100, 640+(i*35), 30, 30), name)
        button.bgcolor = colours[c]
        vowButtons.append(button)
    # diphthongs
    for i,c in enumerate(['41','61','42','82','94']):
        name  = codes[c]
        if inputType == 'txt': name = arpCodes[c]
        button = pygbutton.PygButton((140, 640+(i*35), 30, 30), name)
        button.bgcolor = colours[c]
        vowButtons.append(button)

    if inputType == 'txt':
        for i,c in enumerate(['i','I','1','E','{']):
            button = pygbutton.PygButton((255, 640+(i*40), 30, 30), c)
            button.bgcolor = Color("lightskyblue")
            celexButtons.append(button)

        for i,c in enumerate(['@','3','V','Q']):
            button = pygbutton.PygButton((295, 640+(i*40), 30, 30), c)
            button.bgcolor = Color("lightskyblue")
            celexButtons.append(button)
        
        for i,c in enumerate(['u','U','5','$','#']):
            button = pygbutton.PygButton((335, 640+(i*40), 30, 30), c)
            button.bgcolor = Color("lightskyblue")
            celexButtons.append(button)

        for i,c in enumerate(['2','4','6']):
            button = pygbutton.PygButton((375, 640+(i*40), 30, 30), c)
            button.bgcolor = Color("lightgreen")
            celexButtons.append(button)

        for i,c in enumerate(['7','8','9','H','P']):
            button = pygbutton.PygButton((415, 640+(i*40), 30, 30), c)
            button.bgcolor = Color("lightgreen")
            celexButtons.append(button)
    else:   
        for i,c in enumerate(['High','Mid','Low']):
            button = pygbutton.PygButton((220, 660+(i*40), 70, 30), c)
            button.bgcolor = Color('darkolivegreen2')
            classButtons.append(button) 
        for i,c in enumerate(['Front', 'Centr.', 'Back']):
            button = pygbutton.PygButton((300, 660+(i*40), 70, 30), c)
            button.bgcolor = Color('darkolivegreen2')
            classButtons.append(button) 
        for i,c in enumerate(['Short', 'Long','Diph', 'Rhot']):
            button = pygbutton.PygButton((380, 660+(i*40), 70, 30), c)
            button.bgcolor = Color('darkolivegreen2')
            classButtons.append(button)
        
    sideButtons = ['Show All', 'Clear', 'Play', 'Std Dev', 'Dur.Filter'] 
    if inputType == 'txt': sideButtons += ['Remeasure%']
    else: sideButtons += ['Praat']
    sideButtons += ['Remove', 'Cancel','OK', 'Saved', 'Undo']
    
    lowest = 0
    for i,c in enumerate(sideButtons):
        button = pygbutton.PygButton((705, 10+(i*40), 110, 30), c)
        lowest = 10+(i*40)+40
        button.bgcolor = Color('darkolivegreen2')
        onOffButtons.append(button)    
    
    for i,c in enumerate(['1','2','0']):
        button = pygbutton.PygButton((705+(i*37),lowest, 35, 30), c)
        button.bgcolor = Color('darkolivegreen4')
        onOffButtons.append(button)      

    for i,c in enumerate(['bad Align.','bad Trans.','reduced','other']):
        button = pygbutton.PygButton((705, 640+(i*40), 110, 30), c)
        button.bgcolor = Color('deepskyblue')
        removeButtons.append(button)
    if inputType == 'txt':
        button = pygbutton.PygButton((190,725,30,30),'U')
        button.bgcolor = Color('darkolivegreen2')
        onOffButtons.append(button)
    return (vowButtons,onOffButtons,classButtons,celexButtons,removeButtons)

def loadingMessage(surface, font, message):
    surface.fill(WHITE)
    for i,m in enumerate(message):
        mess = font.render(m,1,BLACK)
        surface.blit(mess,(WINDOWWIDTH/2.0-(font.size(m)[0]/2.0),WINDOWHEIGHT/2.0-(font.size(m)[1]/2.0)+(i*(font.size(m)[1])+5)))
    pygame.display.update()
    surface.fill(WHITE)

def drawGrid(numFont, minmax):
    global DISPLAYSURFACE
    startH = int((580/(maxF1-minF1))*(math.ceil(minF1/50.0)*50 - minF1)+10) 
    intervalH = int((580/(maxF1-minF1))*50)
    startV = WINDOWWIDTH - int((690/(maxF2-minF2))*(math.ceil(minF2/100.0)*100 - minF2) + (WINDOWWIDTH-700))
    intervalV = int((690/(maxF2-minF2))*100)
    h,v = (0,0)

    while True:
        hlimit = startH + h*intervalH
        if hlimit > 590: break
        pygame.draw.line(DISPLAYSURFACE,Color('grey87') ,(10,hlimit),(700,hlimit)) 
        h += 1

    while True:
        vlimit = startV - v*intervalV
        if vlimit < 10: break
        pygame.draw.line(DISPLAYSURFACE,Color('grey87'),(vlimit,590),(vlimit, 10))
        v += 1

    DISPLAYSURFACE.blit(minmax[0],(700-numFont.size(str(int(minF1)))[0],numFont.size(str(int(minF1)))[1]+10))
    DISPLAYSURFACE.blit(minmax[1],(700-numFont.size(str(int(minF2)))[0]-10,10))
    DISPLAYSURFACE.blit(minmax[2],(700-numFont.size(str(int(maxF1)))[0], 590-numFont.size(str(int(minF1)))[1]))
    DISPLAYSURFACE.blit(minmax[3],(12, 10))

    

def main(): 
    global files, myfont, DISPLAYSURFACE
    getFiles()
    mapToCelex.changeCelexPath('support_scripts/celex.cd')
    windowBgColor = WHITE       #set background colour
    pygame.init()               # initialize pygame
    DISPLAYSURFACE = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT)) # create window according to dimensions 
    myfont = pygame.font.SysFont('helvetica',20)    # set font
    numFont = pygame.font.SysFont('helvetica',15)
    allLogs = {f[0]:{} for f in files}
    # main function that implements pygame  
    textListFont = pygame.font.SysFont('courier',18)
    FPSCLOCK = pygame.time.Clock()      #initialize clock 
    caption = 'Plotmish - '+args.k if args.k else 'Plotmish'
    pygame.display.set_caption(caption) # set window caption
    loadingMessage(DISPLAYSURFACE, myfont, ['Loading Vowels'])
    if inputType == 'plt': getVowels() # get all the vowels from the .plt file and write them to the allvowels dictionary
    else: getVowelsTxt()
    minmax = [numFont.render(str(int(i)),1,BLACK) for i in [minF1,minF2,maxF1,maxF2]]
    F1,F2 = (myfont.render('F1',1,Color('grey87')),myfont.render('F2',1,Color('grey87')))
    drawGrid(numFont, minmax)
    permButtons = makeButtons() # make permanent buttons (vowel buttons, display all/none buttons, class buttons)
    permDisplay = permButtons[0]+permButtons[1]+permButtons[2]+permButtons[3] 
    removeButtons = permButtons[4]
    displayRemove = False
    vowButtons =  makeVowels() # makes buttons according to each vowel in the .plt file
    vowButtonList = []
    for v,b in vowButtons.items(): # make a list of all the vowel buttons
        vowButtonList += b
    vowList = [] # list to write vowel that are currently displayed
    textList = [] # list to write the info for the vowel that was scrolled over last
    xFormButtons = [] # list to write the alternate measurements to (when re-evaluating a vowel)
    chooseFormants = False  # True if you are re-evaluating formant measurements 
    currentVowel = None # current vowel button (last scrolled over)
    play = False # indicates whether play button in on or off
    oldv = None # when remeasuring a vowel this stores the old values 
    stdDevCounter = 0
    ellip = []
    formType = 5
    praatMode = False
    praatLog = os.path.join(os.getcwd(),'praatLog')
    call(['rm', praatLog])
    praatInfo = []
    filtered = []
    minDur = None
    stressFiltered = []
    vowelChange = True
    remeasureForms = True
    firstSave = False
    arpDisplayed = []
    celDisplayed = []
    displayMemory = [vowButtonList]
    logMemory = [allLogs]
    vowelMode = 'union'
    while True: # main loop
        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE): # process when quitting plotmish
                call(['rm', praatLog])
                if firstSave:
                    writeLogs(allLogs, True)
                else:
                    writeLogs(allLogs)
                #call(['rm','temp.wav'])
                pygame.quit() 
                sys.exit()            
            # display buttons when clicked
            if not chooseFormants:   
                for b in permButtons[0]: # displays vowels on the screen when the corresponding vowel or diphthong button in clicked
                    if 'click' in b.handleEvent(event):
                        b.font.set_bold(True)
                        b._update()
                        arpDisplayed += [b.caption]
                        textList = []
                        filtered = []
                        minDur = None
                        vowelChange = True

                for b in permButtons[1]: # display all or no vowels on screen if corresponding button in clicked
                    if 'Saved' in b.caption and allLogs != {f[0]:{} for f in files}:
                        b.font.set_bold(False)
                        b.caption = 'Save'
                        vowelChange = True
                    if 'click' in b.handleEvent(event):
                        b.font.set_bold(False)
                        if b.caption == 'Show All':
                            for b in permButtons[0]+permButtons[2]+permButtons[3]:
                                b.font.set_bold(True)
                                b._update()
                            vowList = vowButtonList
                            arpDisplayed = [b.caption for b in permButtons[0]]
                            celDisplayed = [b.caption for b in permButtons[3]]+['NA']
                            filtered = []
                            minDur = None
                            vowelChange = True
                        if b.caption == 'Clear':
                            for b in permButtons[0]+permButtons[2]+permButtons[3]:
                                b.font.set_bold(False)
                                b._update()
                            arpDisplayed = []
                            celDisplayed = []
                            vowList = []
                            textList = []
                            filtered = []
                            minDur = None
                            vowelChange = True
                        if b.caption == 'Play': # start/stop play mode
                            if not play: 
                                play = True
                                b.bgcolor = Color("darkolivegreen4")
                            else: 
                                play = False 
                                b.bgcolor = Color("darkolivegreen2")
                        if 'Std Dev' in b.caption:
                            try:
                                if stdDevCounter == 0:
                                    ellip = confidenceEllipse([form[1] for form in vowList],1, DISPLAYSURFACE)
                                    stdDevCounter = 1
                                    b.caption = 'Std Dev 1'
                                    b.bgcolor = Color("darkolivegreen4")
                                elif stdDevCounter == 1:
                                    ellip = confidenceEllipse([form[1] for form in vowList],2, DISPLAYSURFACE)
                                    stdDevCounter = 2
                                    b.caption = 'Std Dev 2'
                                elif stdDevCounter == 2:
                                    ellip = confidenceEllipse([form[1] for form in vowList],3, DISPLAYSURFACE)
                                    stdDevCounter = 3
                                    b.caption = 'Std Dev 3'
                                
                                else:
                                    ellip = []
                                    b.caption = 'Std Dev'
                                    b.bgcolor = Color("darkolivegreen2")
                                    stdDevCounter = 0
                            except:
                                ellip = []
                                b.caption = 'Std Dev'
                                b.bgcolor = Color("darkolivegreen2")
                                stdDevCounter = 0
                            vowelChange = True
                        if 'Remeasure' in b.caption:
                            if b.caption == 'Remeasure%':
                                formType = 6
                                remeasureForms = True
                                b.caption = 'RemeasureF'
                            elif b.caption == 'RemeasureF':
                                if os.path.isdir(args.p):
                                    praatMode = True
                                    b.caption = 'RemeasureP'
                                else: 
                                    remeasureForms = False
                                    formType = 5
                                    b.caption = 'Remeasure%'
                            else:                        
                                praatMode = False
                                remeasureForms = False
                                formType = 5
                                b.caption = 'Remeasure%'
                        
                        if b.caption == 'Praat':
                            if b.bgcolor == Color('darkolivegreen2'):
                                praatMode = True
                                b.bgcolor = Color('darkolivegreen4')
                            elif b.bgcolor == Color('darkolivegreen4'):
                                praatMode = False
                                b.bgcolor = Color('darkolivegreen2')

                        if b.caption == 'Cancel' and praatMode:
                            call(['support_scripts/sendpraat', '0', 'praat', 'Quit'])

                        if b.caption == 'Dur.Filter':
                            minDur = None
                            while not minDur or minDur != '':    
                                minDur = inputbox.ask(DISPLAYSURFACE,'Minimum Duration (ms)')
                                try:                                    
                                    minDur = int(minDur)
                                    break
                                except: 
                                    if minDur != '': minDur = None
                            if minDur == '': break
                            for v in vowList:
                                if int(v[2][2]) < minDur:
                                    filtered += [v]
                            vowelChange = True
                        
                        if b.caption == 'Remove' and filtered:
                            yesno = None
                            while not yesno:
                                yesno = inputbox.ask(DISPLAYSURFACE,'Remove %r filtered vowels? y/n' % len(filtered)).strip().lower()
                                if yesno not in ['y','n']:
                                    if yesno == 'yes': minDur = 'y'
                                    elif yesno == 'no': minDur = 'n'
                                    else: yesno = None
                            vowelChange = True
                            if yesno == 'n': break
                            for f in filtered:
                                reason = 'filtered: below minimum duration of %d ms' % minDur
                                outCode = codes[f[2][0]] if inputType == 'plt' else arpCodes[f[2][0]]
                                newInfo = [str(wr) for wr in [outCode,f[2][3],f[2][4],f[2][4],f[2][2],f[2][1],'removed '+reason]]
                                if inputType == 'txt': newInfo.insert(6,f[2][10])
                                else: newInfo.insert(6,f[2][6])
                                allLogs[f[1][2]][f[2][4]] = newInfo
                                vowButtonList.remove(f)
                            filtered = []
                            minDur = None
                            vowelChange = True
                        
                        if b.caption in ['1','2','0']:
                            if b.bgcolor == Color("darkolivegreen4"): b.bgcolor = Color("darkolivegreen2")
                            else: b.bgcolor = Color("darkolivegreen4") 
                            vowelChange = True
                        
                        if 'Save' in b.caption:
                            if firstSave:
                                writeLogs(allLogs, True)
                            else:
                                writeLogs(allLogs)
                                firstSave = True
                            allLogs = {f[0]:{} for f in files}
                            b.caption = 'Saved'
                            vowelChange = True
                            displayMemory = [[v for v in vowButtonList]]
                        
                        if 'U'.decode('utf8') == b.caption:
                            vowelMode = 'intersect'
                            b.caption = '∩'.decode('utf8')
                            vowelChange = True
                        elif '∩'.decode('utf8') == b.caption:
                            vowelMode = 'union'
                            b.caption = 'U'.decode('utf8')
                            vowelChange = True

                        if b.caption == 'Undo':
                            try:
                                lastdisplay = displayMemory.pop()
                                vowButtonList = lastdisplay
                                vowelChange = True
                                allLogs = copy.deepcopy(logMemory.pop())
                            except: pass
                            if len(displayMemory) < 2: displayMemory = [[v for v in vowButtonList]]
                            if len(logMemory) <2: logMemory = [copy.deepcopy(allLogs)]
                ###GET RID OF VOWEL CLASSES FOR PLT OR IMPLEMENT INTERSECT/ UNION
                for b in permButtons[2]: # displays vowels on the screen when the corresponding class button in clicked
                    if 'click' in b.handleEvent(event):
                        b.font.set_bold(True)
                        b._update()
                        for cl in classes[b.caption]:
                            try: arpDisplayed +=[codes[cl]]
                            except: pass
                        textList = []
                        filtered = []
                        minDur = None
                        vowelChange = True

                for b in permButtons[3]:
                    if 'click' in b.handleEvent(event):
                        b.font.set_bold(True)
                        b._update()
                        celDisplayed += [b.caption]
                        textList = []
                        filtered = []
                        minDur = None
                        vowelChange = True
                
                if vowelChange:
                    vowList = []
                    if inputType == 'txt':
                        if vowelMode == 'intersect':
                            for v in vowButtonList:    
                                    if (arpCodes[v[2][0]] in arpDisplayed) and (v[2][7] in celDisplayed):
                                        vowList += [v] if v not in filtered else []
                        else: 
                            for v in vowButtonList:    
                                    if (arpCodes[v[2][0]] in arpDisplayed) or (v[2][7] in celDisplayed):
                                        vowList += [v] if  v not in filtered else []
                    else: 
                        for b in permButtons[0]:
                            for v in vowButtonList:
                                vowList += [v] if b.bgcolor == v[0].fgcolor and b.caption in arpDisplayed and v not in filtered else []


                if currentVowel:
                    if 'click' in currentVowel[0].handleEvent(event):
                        displayMemory += [[v for v in vowButtonList]]
                        logMemory += [copy.deepcopy(allLogs)]
                        if praatMode:
                            zoomMin = str(float(currentVowel[2][4])-0.25)
                            zoomMax = str(float(currentVowel[2][4])+0.25)
                            message = 'runScript: \"support_scripts/zoomIn.praat\", %r, %r' % (currentVowel[1][2],float(currentVowel[2][4]))
                            call(['open', args.p])
                            call(['support_scripts/sendpraat', '0', 'praat', 'execute \"'+os.path.join(os.getcwd(),'support_scripts/zoomIn.praat')+'\" \"' + currentVowel[1][2] + '\" \"'+os.path.join(os.getcwd(),'praatLog')+ '\" ' + currentVowel[2][4] + '"'])  
                            chooseFormants = True
                            break
                            
                        f,g = currentVowel[1],currentVowel[2]
                        for xform in currentVowel[2][formType]: # figure out where to write the alternate formant buttons
                            x,y = calculateVowelLocation(xform)
                            buttonRect = pygame.Rect(x,y, 8, 8)
                            buttonRect.center = (x,y)
                            button = (pygbutton.PygButton(buttonRect, '►'.decode('utf8'),border = False),xform) # make new button for each alternate formant
                            button[0].bgcolor = BLACK # set colour of alternate formants to black
                            button[0].fgcolor = BLACK
                            xFormButtons += [(button,currentVowel)]
                        x,y = calculateVowelLocation(currentVowel[1])
                        buttonRect = pygame.Rect(x,y, 10, 10)
                        buttonRect.center = (x,y)
                        currVowelButton = (pygbutton.PygButton(buttonRect, '◉'.decode('utf8'), border = False),currentVowel[1])
                        currVowelButton[0].bgcolor = WHITE 
                        currVowelButton[0].fgcolor = currentVowel[0].fgcolor
                        xFormButtons += [(currVowelButton,currentVowel)]
                        chooseFormants = True

                for v in vowList: # deal with all vowels currently displayed on screen
                    if 'enter' in v[0].handleEvent(event):
                        f,g = v[1],v[2]
                        # write the vowel information to the display bit (lower right of the screen)
                        vname = arpCodes[g[0]].upper() if inputType == 'txt' else codes[g[0]]
                        textList = ['vowel: '+vname,'F1: '+str(f[0]),
                                     'F2: '+str(f[1]),'stress: '+str(g[1]),
                                     'duration: '+str(g[2])+' ms','word: '+g[3],
                                     'time: '+g[4]]
                        currentVowel = v
                        if args.f0: textList += ['pitch: '+g[11]]
                        if inputType == 'txt': 
                            textList.insert(1,'celex: '+g[7])
                            textList.insert(-1,'environ: '+g[8]+' v '+g[9])
                            textList.insert(-1,'max formants: '+g[10])
                        if play: # play the vowel sound (if play mode is on), plays 25 milliseconds on either side of measurement point
                            call(['play',f[2],'trim',str(float(g[4])-0.1), '='+str(float(g[4])+0.1)])   
                

            else:
                if praatMode and os.path.isfile(praatLog):
                    praatInfo = [(p.split()[0].strip(), p.split()[1].strip() ,p.split()[2].strip(), p.split()[3].strip()) for p in open(praatLog,'rU').readlines()]
                    call(['rm',praatLog])
                if praatInfo:
                    oldInfo = [currentVowel[2][4], currentVowel[1][0], currentVowel[1][1]]
                    if args.f0: oldInfo += currentVowel[2][11]
                    praatInfo += [tuple(oldInfo)]
                    for p in praatInfo:
                        x,y = calculateVowelLocation((float(p[1]),float(p[2])))
                        tempCurr = list(currentVowel)
                        tempCurr[2] = list(tempCurr[2])
                        tempCurr[2][4] = str(round(float(p[0]),3))
                        if args.f0: tempCurr[2][11] = str(p[3]) 
                        tempCurr[2] = tuple(tempCurr[2])
                        tempCurr[1] = list(tempCurr[1])
                        tempCurr[1][0] = p[1]
                        tempCurr[1][1] = p[2]
                        tempCurr[1] = tuple(tempCurr[1])
                        if p != praatInfo[-1]:
                            buttonRect = pygame.Rect(x,y, 8, 8)
                            buttonRect.center = (x,y)
                            currVowelButton = (pygbutton.PygButton(buttonRect, '►'.decode('utf8'), border = False),tempCurr[1])
                            currVowelButton[0].bgcolor = BLACK
                            currVowelButton[0].fgcolor = BLACK 
                        else:
                            buttonRect = pygame.Rect(x,y, 10, 10)
                            buttonRect.center = (x,y)
                            currVowelButton = (pygbutton.PygButton(buttonRect, '◉'.decode('utf8'), border = False),tempCurr[1])
                            currVowelButton[0].bgcolor = WHITE
                            currVowelButton[0].fgcolor = currentVowel[0].fgcolor 
                        xFormButtons += [(currVowelButton,tuple(tempCurr))]
                    praatInfo = []


                for b in permButtons[1]:
                    if 'click' in b.handleEvent(event):
                        if 'Remove' in b.caption:
                            displayRemove = True
                            call(['support_scripts/sendpraat', '0', 'praat', 'Quit'])
                            vowelChange = True

                        if 'Cancel'in b.caption:
                            xFormButtons = []
                            chooseFormants = False
                            displayRemove = False
                            call(['support_scripts/sendpraat', '0', 'praat', 'Quit'])
                            vowelChange = True

                        if b.caption == 'OK':
                            xFormButtons = []
                            chooseFormants = False
                            displayRemove = False
                            call(['support_scripts/sendpraat', '0', 'praat', 'Quit'])
                            vowelChange = True
                            currentVowel[0].bgcolor = WHITE
                            answer = inputbox.ask(DISPLAYSURFACE,'Comment')
                            if answer:
                                outCode = codes[currentVowel[2][0]] if inputType == 'plt' else arpCodes[currentVowel[2][0]]
                                newInfo = [str(wr) for wr in [outCode,currentVowel[2][3],currentVowel[2][4],currentVowel[2][4],currentVowel[2][2],currentVowel[2][1],'OK '+answer]]
                                if inputType == 'txt': newInfo.insert(6,currentVowel[2][10])
                                else:  newInfo.insert(6,currentVowel[2][6])
                                allLogs[currentVowel[1][2]][currentVowel[2][4]] = newInfo



                            
                for b in removeButtons:
                    if 'click' in b.handleEvent(event) and displayRemove:
                        reason = b.caption if b.caption != 'other' else inputbox.ask(DISPLAYSURFACE,'Other')
                        outCode = codes[currentVowel[2][0]] if inputType == 'plt' else arpCodes[currentVowel[2][0]]
                        newInfo = [str(wr) for wr in [outCode,currentVowel[2][3],currentVowel[2][4],currentVowel[2][4],currentVowel[2][2],currentVowel[2][1],'removed '+reason]]
                        if inputType == 'txt': newInfo.insert(6,currentVowel[2][10])
                        else:  newInfo.insert(6,currentVowel[2][6])
                        allLogs[currentVowel[1][2]][currentVowel[2][4]] = newInfo
                        vowButtonList.remove(currentVowel)
                        vowList.remove(currentVowel)
                        currentVowel = []
                        textList = []
                        xFormButtons = []
                        chooseFormants = False
                        displayRemove = False
                        vowelChange = True

                
                for x in xFormButtons: # choose new formant
                    if 'click' in x[0][0].handleEvent(event): # click on black or white button to set new vowel location 
                        for vb in vowButtonList:
                            if vb[0] is x[1][0]:
                                oldv = vb
                                x[0][0].fgcolor = vb[0].bgcolor if vb[0].bgcolor != WHITE else vb[0].fgcolor
                                x[0][0].bgcolor = WHITE
                                if x[0][0].caption != '►'.decode('utf8'):
                                    x[0][0].caption = '►'.decode('utf8')
                                    b.rect = b.rect.inflate(-1,-1)
                                redoSpecs = tuple([x[0][1][0],x[0][1][1],x[1][1][2]]) 
                                tempvb = tuple([x[0][0],redoSpecs]+list(x[1][2:]))
                                vowButtonList.remove(vb)
                                vowButtonList.append(tempvb)
                                vowList.remove(vb)
                                vowList.append(tempvb)
                                currentVowel = tempvb
                                call(['support_scripts/sendpraat', '0', 'praat', 'Quit'])
                        # write the information of the changed vowel to the list (to write to the log file later)
                        outCode = codes[tempvb[2][0]] if inputType == 'plt' else arpCodes[tempvb[2][0]]
                        if inputType == 'txt':
                            formantNum = oldv[2][10]
                        else:
                            formantNum = oldv[2][6]
                        if praatMode or remeasureForms: 
                            formantNum = 'unknown'
                        newInfo = [str(wr) for wr in [outCode,tempvb[2][3],oldv[2][4],tempvb[2][4],tempvb[2][2],tempvb[2][1],formantNum,oldv[1][0],tempvb[1][0],oldv[1][1],tempvb[1][1]]]
                        allLogs[oldv[1][2]][tempvb[2][4]] = newInfo
                        chooseFormants = False
                        xFormButtons = []
                        vname = arpCodes[tempvb[2][0]].upper() if inputType == 'txt' else codes[tempvb[2][0]]

                        textList = ['vowel: '+vname,'F1: '+str(tempvb[1][0]),
                                     'F2: '+str(tempvb[1][1]),'stress: '+tempvb[2][1],
                                     'duration: '+tempvb[2][2]+' ms','word: '+tempvb[2][3],
                                     'time: '+tempvb[2][4]]
                        if args.f0: textList += ['pitch: '+ tempvb[2][11]]
                        if inputType == 'txt': 
                            textList.insert(1,'celex: '+tempvb[2][9])
                            textList += ['environ.: '+tempvb[2][8]+' v '+tempvb[2][9]]
                            textList += ['max formants: '+tempvb[2][10]]
                        praatInfo = []              
                        vowelChange = True
        
        for b in permButtons[1]:
            if b.caption in ['1','2','0']:
                if filtered: b.bgcolor = Color("darkolivegreen4")
                if b.bgcolor == Color("darkolivegreen2"):                            
                    stressFiltered += [b.caption]

            
             
        vowList = [v for v in vowList if v[2][1] not in stressFiltered]
        stressFiltered = []
        if vowelChange:
            DISPLAYSURFACE.fill(windowBgColor)
        else: 
            for r in NOTPLOTRECTS:
                pygame.draw.rect(DISPLAYSURFACE,WHITE,r)
        
        if ellip and vowelChange: DISPLAYSURFACE.blit(ellip[0],ellip[1])
        pygame.draw.lines(DISPLAYSURFACE,BLACK,True,[(490,600),(700,600),(700,840),(490,840)],2) # draw rectangle to display vowel info
        pygame.draw.lines(DISPLAYSURFACE,BLACK,True, [(10,10),(700,10),(700,590),(10,590)],2) # draw rectangle to display vowel buttons
        tokenNum = myfont.render(str(len(vowList)),1,BLACK)
        DISPLAYSURFACE.blit(tokenNum,(710,820))
        pygame.draw.lines(DISPLAYSURFACE,BLACK,True,[(10,630),(185,630),(185,840),(10,840)],2)
        
        if minDur:
            minNum = myfont.render(str(minDur),1,BLACK)
            DISPLAYSURFACE.blit(minNum,(710,800))
        
        if inputType == 'txt':
            pygame.draw.lines(DISPLAYSURFACE,BLACK,True,[(225,630),(480,630),(480,840),(225,840)],2)
            celLabel = myfont.render('CELEX',1,BLACK)
            DISPLAYSURFACE.blit(celLabel,(320,605))
            arpLabel = myfont.render('ARPABET',1,BLACK)
            DISPLAYSURFACE.blit(arpLabel,(50,605))
        
        if displayRemove:
            for b in removeButtons:
                b.draw(DISPLAYSURFACE)
        
        for b in permDisplay: # draw vowels to screen
            b.draw(DISPLAYSURFACE)
        
        if textList:    # draw info for last vowel scrolled over to screen
            for i,t in enumerate(textList):
                label = textListFont.render(t, 1, BLACK)
                DISPLAYSURFACE.blit(label, (500, 605+(21*i)))
        
        if chooseFormants: # draw alternate formant buttons (when in choose formant mode)
            for xf in xFormButtons:
                xf[0][0].draw(DISPLAYSURFACE)
        
        if vowelChange:
            DISPLAYSURFACE.blit(F1,(PLOTWIDTH-myfont.size('F1')[0],PLOTBOTTOM/2))
            DISPLAYSURFACE.blit(F2,(PLOTWIDTH/2,10))
            drawGrid(numFont, minmax)
            for b in [v[0] for v in vowList]:
                b.draw(DISPLAYSURFACE)
            vowelChange = False
        
        pygame.display.update() # update screen
        FPSCLOCK.tick(FPS) # screen updates at 30 frames per second


if __name__ == '__main__':
    main()