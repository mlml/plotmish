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
from subprocess import call, Popen
if os.path.isdir('plotmish'):
    os.chdir('plotmish')
sys.path.append('support_scripts')
import pygbutton, inputbox, mapToCelex
from pygame.locals import *

import numpy as np

global vowByCode, vowByClass, codes, classes, maxF1,maxF2,minF1,minF2, allvowels, inputType, files, pitchFiles, myfont, DISPLAYSURFACE, maxMin, allLogs, remReason

#set window sizes and frames per second
FPS = 10
WINDOWWIDTH = 820
PLOTWIDTH = 700
WINDOWHEIGHT = 850
PLOTBOTTOM = 600
NOTPLOTRECTS = (pygame.Rect(PLOTWIDTH,0,WINDOWWIDTH - PLOTWIDTH, PLOTBOTTOM),
                pygame.Rect(0,PLOTBOTTOM,WINDOWWIDTH,WINDOWHEIGHT - PLOTBOTTOM))

class vowel:
    def __init__(self, f1, f2, wfile):
        self.vowelCode = ''
        self.F1 = f1
        self.F2 = f2
        self.wFile = wfile
        self.stress = None
        self.duration = None
        self.word = ''
        self.time = None
        self.celex = ''
        self.pPhone = ''
        self.fPhone = ''
        self.maxForm = ''
        self.timeRange = ()
        self.durForms = []
        self.numForms = []
        self.pitch = None
        self.button = None
        self.origButton = None
        self.alreadyCorrected = None
        self.id = None

    def makeAlternate(self, f1, f2, newButton):
        newV = vowel(f1,f2, self.wFile)
        newV.vowelCode = self.vowelCode
        newV.stress = self.stress
        newV.duration = self.duration
        newV.word = self.word
        newV.time = self.time
        newV.celex = self.celex
        newV.pPhone = self.pPhone
        newV.fPhone = self.fPhone
        newV.maxForm = self.maxForm
        newV.durForms = self.durForms
        newV.numForms = self.numForms
        newV.timeRange = self.timeRange
        newV.pitch = self.pitch
        newV.id = self.id
        newV.F1 = f1
        newV.F2 = f2
        newV.origButton = self.button
        newV.button = newButton
        return newV

#set default black and white colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# parse in arguments from the command line
parser = argparse.ArgumentParser(description = 'Make blank textgrids for transcription of DR uncut clips')
parser.add_argument('vowels', metavar = 'vowel info', help = '.plt file or formant.txt file or folder containing many')
parser.add_argument('wav', metavar = 'wav file', help = '.wav file or folder containing many')
parser.add_argument('annotator', metavar = 'annotator', help = 'what\'s your name?')
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
            if header: log.writerow(['annotator','id','vowel','word','oldTime','time','duration (ms)','stress','maxForms','oldF1','F1','oldF2','F2'])
        else:
            log = csv.writer(open(os.path.join(args.o,os.path.basename(f).replace('.wav','-corrLog.csv')),'wb'))
            log.writerow(['annotator','id','vowel','word','oldTime','time','duration (ms)','stress','maxForms','oldF1','F1','oldF2','F2'])

        # write header to log file
        for k,w in writeThis.items():
            log.writerow([args.annotator]+[w[0].split('-')[-1]]+w[1:])

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
        '''
        response = ''
        while response not in ['p','t']:
            response = raw_input('Found both text files and plotnik files \nWhich file type do you want to use? \n(p)lotnik or (t)ext:  ') 
        response = '.plt' if response == 'p' else 'formant.txt'
        '''
        response = pltOrTxt()
        files = [f for f in files if response in f[1]]
    assert files, 'ERROR: no files found'
    inputType = 'plt' if '.plt' in files[0][1] else 'txt'


def pltOrTxt():
    message = ['Found both text files and plotnik files','Which file type do you want to use?', 'Text files are recomended']
    loadingMessage(DISPLAYSURFACE,myfont,message)
    ptButtons = [pygbutton.PygButton((WINDOWWIDTH/2.0 - 120, WINDOWHEIGHT/2.0 + 80, 60, 30), caption = 'text', font = myfont),pygbutton.PygButton((WINDOWWIDTH/2.0 +60, WINDOWHEIGHT/2.0 + 80, 60, 30), caption = 'plotnik', font = myfont)]
    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit() 
                sys.exit()
            for b in ptButtons:
                if 'click' in b.handleEvent(event):
                    return '.plt' if b.caption == 'plotnik' else 'formant.txt'
        for b in ptButtons:
            b.draw(DISPLAYSURFACE)
        pygame.display.update() # update screen
        FPSCLOCK.tick(FPS)

def calculateVowelLocation(f):
    # calculates the location to display the vowel based on tuple of (F1,F2) 
    #if maxMin == (minF1,minF2,maxF1,maxF2): tempMaxMin = (maxMin[0]-maxMin[2]*0.05, maxMin[1]-maxMin[3]*0.05, maxMin[2]+maxMin[2]*0.05, maxMin[3]+maxMin[3]*0.05)
    #else: tempMaxMin = maxMin    
    tempMaxMin = maxMin
    x = (((tempMaxMin[3]-float(f[1])))/(tempMaxMin[3]-tempMaxMin[1]))*(PLOTWIDTH-20)+10 
    y = ((float(f[0]) - tempMaxMin[0])/(tempMaxMin[2]-tempMaxMin[0]))*(PLOTBOTTOM-20)+10
    return (x,y)


def makeVowels():
    # makes buttons for the initial vowels and assigns colours
    vowButtons = {}
    for v in allvowels:
        x,y = calculateVowelLocation((v.F1,v.F2))
        buttonRect = pygame.Rect(x,y, 8, 8)
        buttonRect.center = (x,y)
        button = pygbutton.PygButton(buttonRect,'►'.decode('utf8'),border = False)
        button.bgcolor = colours[v.vowelCode] 
        button.fgcolor = colours[v.vowelCode]
        v.button = button
        if v.vowelCode not in vowButtons:
            vowButtons.update({v.vowelCode:[v]})
        else:
            vowButtons[v.vowelCode] += [v] 
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
    allvowels = []
    for f in files:
        # display which file is being processed TODO: speed this up
        loadingMessage(DISPLAYSURFACE, myfont, ['Loading Vowels', os.path.basename(f[0]).replace('.wav','')])
        # get pitch track if f0 is specified as an argument (from the command line)
        if args.f0: 
            thisPitch = [p for p in pitchFiles if os.path.basename(p).replace('.Pitch','') in os.path.basename(f[0])][0]
            pitchList = [p.replace('\n','').strip() for p in open(thisPitch,'rU').readlines()]
        vowelF = open(f[1],'r')
        vowels = vowelF.readlines()[3:]
        #get associated log file if available
        try:
            logF = open(os.path.join(args.o , os.path.basename(f[0]).replace('.wav','')+'-corrLog.csv'),'rU')
            logR = list(csv.reader(logF))[1:]
            logF.close()
        except: 
            logR = None    

        for i,v in enumerate(vowels):
            v = v.split('\t')
            nV = vowel(float(v[3]),float(v[4]),f[0]) # initialize new vowel
            # get other formant measurements from various points in the vowel duration  
            # (F1@20%, F2@20%, F1@35%, F2@35%, F1@50%, F2@50%, F1@65%, F2@65%, F1@80%, F2@80%)
            nV.id = os.path.basename(f[0]).replace('.wav','')+'-'+str(i+1)
            extraForms = tuple(v[21:31])
            for j in range(0,len(extraForms),2):
                try: nV.durForms += [(round(float(extraForms[j]),1),round(float(extraForms[j+1]),1))]
                except: continue 
            # get other formant measurements from the same point with various max Formant settings (3,4,5,6)
            moreForms = [re.sub('[\[\]]','',m).split(',') for m in v[36].split('],[')]
            for m in moreForms:
                try:
                    temp = [tuple([round(float(n.strip()),1) for n in m[:2]])]
                except: 
                    assert False, 'ERROR:\tthe formant.txt files do not contain extra formant measurement info\n\t\t\tmake sure the config.txt file in FAVE-extract has the line:\n\t\t\tcandidates=T\n\t\t\tand then re-extract the formant values'
                if len(temp[0]) != 2:
                    continue
                nV.numForms += temp
            cmuPron = [p.strip() for p in re.sub('[\[\]\']','',v[33]).split(',')]
            nV.pPhone = v[31]
            nV.fPhone = v[32]
            nV.word = v[2]
            vIndex = int(v[34])
            nV.celex = getCelexVowel(nV.word,cmuPron,vIndex)
            nV.time = v[9]
            if args.f0: nV.pitch = getPitch(pitchList,timestamp, thisPitch) 
            nV.maxForm = v[35]
            nV.vowelCode = revArpCodes[v[0].strip()]
            nV.stress = v[1]
            nV.timeRange = (v[10],v[11])
            nV.duration = str(int(float(v[12])*1000))
            nV.wFile = f[0]
            if logR:
                for line in logR:
                    if line[1].strip() == str(i+1):
                        try:
                            if not line[13].strip():
                                nV.alreadyCorrected = (line[5], line[8], line[10], line[12])
                            else:
                                nV.alreadyCorrected = 'removed'
                        except: 
                            nV.alreadyCorrected = (line[5], line[8], line[10], line[12])
                        print nV.time, nV.maxForm, nV.F1, nV.F2
                                        
            '''
            try: 
                if nV[38].strip():
                    nV.alreadyCorrected = True
            except: pass
            '''

            allvowels += [nV]
        #makeVowelClasses()
        # gets the max and min F1 and F2 
    maxF1 = max([float(f.F1) for f in allvowels])
    minF1 = min([float(f.F1) for f in allvowels])
    maxF2 = max([float(f.F2) for f in allvowels])
    minF2 = min([float(f.F2) for f in allvowels])


def getVowels():
    # reads all the vowels from the .plt file 
    global allvowels, maxF1,maxF2,minF1,minF2, myfont, DISPLAYSURFACE
    allvowels = []
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
            v = v.split(',')
            nV = vowel(float(v[0]),float(v[1]),f[0])
            # get other formant measurements from various points in the vowel duration  
            # (F1@20%, F2@20%, F1@35%, F2@35%, F1@50%, F2@50%, F1@65%, F2@65%, F1@80%, F2@80%)
            extraForms = re.sub('[<>]','',extraFormants[i][0])
            extraForms = extraForms.split(',')
            nV.durForms = []
            nV.id = os.path.basename(f[0]).replace('.wav','')+'-'+str(i+1)
            for i in range(0,len(extraForms),2):
                try: nV.durForms += [(round(float(extraForms[i]),1),round(float(extraForms[i+1]),1))]
                except: continue 
            nV.word = v[5].split()[0]
            nV.maxForm = v[5].split()[1].replace('/','')
            nV.timestamp = v[5].split()[-1]
            if args.f0: nV.pitch = getPitch(pitchList,timestamp, thisPitch)
            # (F1, F2) = (vowelCode,stress,duration,word,timestamp,(extra formants))
            nV.vowelCode = v[3].split('.')[0]
            stress = v[4].split('.')[0]
            nV.stress = '0' if stress == '3' else stress
            nV.duration = v[4].split('.')[1]
            allvowels += [nV]
        makeVowelClasses()
        # gets the max and min F1 and F2 
    maxF1 = max([float(f.F1) for f in allvowels])
    minF1 = min([float(f.F1) for f in allvowels])
    maxF2 = max([float(f.F2) for f in allvowels])
    minF2 = min([float(f.F2) for f in allvowels])

def makeVowelClasses():
    # sorts vowesl in allvowels in to classes
    vowByCode = {k:{} for k in codes.keys()}
    vowByClass = {k:{} for k in classes.keys()}
    for v in allvowels:
        vowByCode[v.vowelCode].update({f:v})
        for names, nums in classes.items():
            if v.vowelCode in nums:
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
        button = pygbutton.PygButton((190,720,30,30),'U'.decode('utf8'))
        button.bgcolor = Color('darkolivegreen2')
        button.font = myfont
        onOffButtons.append(button)
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
        
    sideButtons = ['Show All', 'Clear', 'Play', 'Std Dev', 'Dur.Filter', 'Zoom'] 
    if inputType == 'txt': sideButtons += ['RemeasureP']
    else: sideButtons += ['Praat']
    sideButtons += ['Cancel', 'Saved', 'Undo', 'Check Last', 'Rmv. Bad']
    if inputType == 'txt': sideButtons += ['Resume']
    
    lowest = 0
    for i,c in enumerate(sideButtons):
        button = pygbutton.PygButton((705, 10+(i*40), 110, 30), c)
        lowest = 10+(i*40)+40
        if button.caption == 'Rmv. Bad': button.bgcolor = Color('red')
        else: button.bgcolor = Color('darkolivegreen2')
        onOffButtons.append(button)    
    
    for i,c in enumerate(['1','2','0']):
        button = pygbutton.PygButton((705+(i*37),lowest, 35, 30), c)
        button.bgcolor = Color('darkolivegreen4')
        onOffButtons.append(button)      

    return (vowButtons,onOffButtons,classButtons,celexButtons)

def loadingMessage(surface, font, message):
    surface.fill(WHITE)
    for i,m in enumerate(message):
        mess = font.render(m,1,BLACK)
        surface.blit(mess,(WINDOWWIDTH/2.0-(font.size(m)[0]/2.0),WINDOWHEIGHT/2.0-(font.size(m)[1]/2.0)+(i*(font.size(m)[1])+5)))
    pygame.display.update()
    #surface.fill(WHITE)

def drawGrid(numFont):
    global DISPLAYSURFACE
    if maxMin == (minF1,minF2,maxF1,maxF2) : 
        tempMaxMin = (maxMin[0]-maxMin[2]*0.05, maxMin[1]-maxMin[3]*0.05, maxMin[2]+maxMin[2]*0.05, maxMin[3]+maxMin[3]*0.05)
        #tempMaxMin = maxMin
        #startV,startH = calculateVowelLocation((math.ceil(tempMaxMin[1]/100.0)*100 , math.ceil(tempMaxMin[0]/50.0)*50))
    else: 
        tempMaxMin = maxMin
        #startV,startH = calculateVowelLocation((math.ceil(tempMaxMin[1]/100.0)*100 , math.ceil(tempMaxMin[0]/50.0)*50))
    tempMaxMin = maxMin
    intervalH = int(((PLOTBOTTOM-10)/(tempMaxMin[2]-tempMaxMin[0]))*50)
    startH = int(((PLOTBOTTOM-10)/(tempMaxMin[2]-tempMaxMin[0]))*(math.ceil(tempMaxMin[0]/50.0)*50 - tempMaxMin[0])+10)
    startV = WINDOWWIDTH - int(((PLOTWIDTH-10)/(tempMaxMin[3]-tempMaxMin[1]))*(math.ceil(tempMaxMin[1]/100.0)*100 - tempMaxMin[1]) + (WINDOWWIDTH-PLOTWIDTH))
    intervalV = int(((PLOTWIDTH-10)/(tempMaxMin[3]-tempMaxMin[1]))*100)
    h,v = (0,0)
    while True:
        hlimit = startH + h*intervalH
        if hlimit > PLOTBOTTOM: break
        pygame.draw.line(DISPLAYSURFACE,Color('grey87') ,(10,hlimit),(PLOTWIDTH,hlimit)) 
        h += 1
    while True:
        vlimit = startV - v*intervalV
        if vlimit < 10: break
        pygame.draw.line(DISPLAYSURFACE,Color('grey87'),(vlimit,PLOTBOTTOM),(vlimit, 10))
        v += 1
    fontMaxMin = [numFont.render(str(int(i)),1,BLACK) for i in tempMaxMin]
    DISPLAYSURFACE.blit(fontMaxMin[0],(PLOTWIDTH-numFont.size(str(int(minF1)))[0],numFont.size(str(int(minF1)))[1]+10))
    DISPLAYSURFACE.blit(fontMaxMin[1],(PLOTWIDTH-numFont.size(str(int(minF2)))[0]-10,10))
    DISPLAYSURFACE.blit(fontMaxMin[2],(PLOTWIDTH-numFont.size(str(int(maxF1)))[0], PLOTBOTTOM-numFont.size(str(int(minF1)))[1]))
    DISPLAYSURFACE.blit(fontMaxMin[3],(12, 10))


def resize(tempMaxMin, vowButtonList, currentVowel):
    global maxMin
    if tempMaxMin != (minF1,minF2,maxF1,maxF2):
        temp = [None,None,None,None]
        temp[0] = (maxF1-minF1)*(tempMaxMin[0]/float(PLOTBOTTOM-10))+minF1
        temp[1] = maxF2-((maxF2-minF2)*(tempMaxMin[1]/float(PLOTWIDTH-10)))
        temp[2] = (maxF1-minF1)*(tempMaxMin[2]/float(PLOTBOTTOM-10))+minF1
        temp[3] = maxF2-((maxF2-minF2)*(tempMaxMin[3]/float(PLOTWIDTH-10)))    
        maxMin = tuple(temp)
    else: 
        maxMin = (minF1,minF2,maxF1,maxF2)
    for v in vowButtonList:
        x,y = calculateVowelLocation((v.F1,v.F2))
        v.button.rect.center = (x,y)
    if currentVowel:
        x,y = calculateVowelLocation((currentVowel.F1,currentVowel.F2))
        currentVowel.button.rect.center = (x,y)
    return (vowButtonList, currentVowel)

def clearRange(tempMaxMin, vowButtonList, currentVowel, reason):
    tempVBL, tempVL = [],[]
    for v in vowButtonList:
        x,y = v.button.rect.center
        if not (y > tempMaxMin[0] and x < tempMaxMin[1] and y < tempMaxMin[2] and x > tempMaxMin[3]):
            tempVBL += [v]
        else:
            clear(v, reason)
    if currentVowel:
        x,y = currentVowel.button.rect.center
        currentVowel = currentVowel if not (y > tempMaxMin[0] and x < tempMaxMin[1] and y < tempMaxMin[2] and x > tempMaxMin[3]) else None 
    return (tempVBL, currentVowel) 


def clear(currentVowel, reason):
    global allLogs, remReason                           
    outCode = codes[currentVowel.vowelCode] if inputType == 'plt' else arpCodes[currentVowel.vowelCode]
    because = 'unallowed variant' if not remReason and not reason else remReason+' '+reason
    because = 'removed: '+because if not remReason else because
    newInfo = [str(wr) for wr in [currentVowel.id, outCode,currentVowel.word,'NA',currentVowel.time,currentVowel.duration,currentVowel.stress,currentVowel.maxForm,'NA','NA','NA','NA',because]]
    allLogs[currentVowel.wFile][currentVowel.time] = newInfo 


def main(): 
    global files, myfont, DISPLAYSURFACE, FPS, maxMin, allLogs, remReason, FPSCLOCK
    windowBgColor = WHITE       #set background colour
    pygame.init()               # initialize pygame
    FPSCLOCK = pygame.time.Clock()      #initialize clock 
    DISPLAYSURFACE = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT)) # create window according to dimensions 
    myfont = pygame.font.SysFont('helvetica',20)    # set font
    numFont = pygame.font.SysFont('helvetica',15)
    getFiles()
    mapToCelex.changeCelexPath('support_scripts/celex.cd')
    allLogs = {f[0]:{} for f in files}
    # main function that implements pygame  
    textListFont = pygame.font.SysFont('courier',18)
    caption = 'Plotmish - '+args.k if args.k else 'Plotmish'
    pygame.display.set_caption(caption) # set window caption
    loadingMessage(DISPLAYSURFACE, myfont, ['Loading Vowels'])
    if inputType == 'plt': getVowels() # get all the vowels from the .plt file and write them to the allvowels dictionary
    else: getVowelsTxt()
    maxMin = (minF1,minF2,maxF1,maxF2)
    F1,F2 = (myfont.render('F1',1,Color('grey87')),myfont.render('F2',1,Color('grey87')))
    drawGrid(numFont)
    permButtons = makeButtons() # make permanent buttons (vowel buttons, display all/none buttons, class buttons)
    permDisplay = permButtons[0]+permButtons[1]+permButtons[2]+permButtons[3] 
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
    formType = 'dur'
    praatMode = True if os.path.isdir(args.p) else False
    praatLog = os.path.join(os.getcwd(),'praatLog')
    call(['rm', praatLog])
    praatInfo = []
    filtered = []
    minDur = None
    stressFiltered = []
    vowelChange = True
    firstSave = False
    arpDisplayed = []
    celDisplayed = []
    displayMemory = [vowButtonList]
    logMemory = [allLogs]
    vowelMode = 'union'
    remReason = ''
    zooming = False
    start, stop = (),()
    zoomLines = None
    ctrl = [K_RCTRL, K_LCTRL] 
    shft = [K_RSHIFT, K_LSHIFT]
    lastVowel = None
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
            pressed = pygame.key.get_pressed()
            pressCTRLA = (pressed[ctrl[0]] or pressed[ctrl[1]]) and pressed[K_a]
            if zooming or pressCTRLA:
                T,L,B,R = None,None,None,None 
                if event.type == MOUSEBUTTONDOWN:
                    start = pygame.mouse.get_pos()
                    FPS = 50
                elif start: 
                    stop = pygame.mouse.get_pos() 
                    L,R = (start[0],stop[0]) if start[0] < stop[0] else (stop[0],start[0])
                    T,B = (start[1],stop[1]) if start[1] < stop[1] else (stop[1],start[1])
                    zoomLines = [(L,T),(R,T),(R,B),(L,B)]
                    vowelChange = True                    
                    if event.type == MOUSEBUTTONUP:
                        if not (L < 10 or R > PLOTWIDTH or T < 10 or B > PLOTBOTTOM or T == B or L == R):
                            FPS = 10
                            if pressCTRLA:
                                reason = ''
                                if (pressed[shft[0]] or pressed[shft[1]]): 
                                    while not reason or reason == 'QUITNOW':
                                        reason = inputbox.ask(DISPLAYSURFACE,'Reason ')
                                displayMemory += [[v for v in vowButtonList]]
                                logMemory += [copy.deepcopy(allLogs)]
                                vowButtonList, currentVowel = clearRange((T,R,B,L), vowButtonList, currentVowel, reason)
                                if not currentVowel: textList = []
                            else:
                                vowButtonList, currentVowel = resize((T,R,B,L), vowButtonList, currentVowel)
                                for b in permButtons[1]:
                                    if b.caption == 'Zoom':
                                        b.caption = 'Reset Zoom'
                                        b.font.set_bold(False)
                        zoomLines = None
                        start, stop = (),()

            if not chooseFormants:   
                for b in permButtons[0]: # displays vowels on the screen when the corresponding vowel or diphthong button in clicked
                    if 'click' in b.handleEvent(event):
                        if b.caption in arpDisplayed:
                            b.font.set_bold(False)
                            b._update()
                            arpDisplayed.remove(b.caption)
                        else:
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
                    if b.caption == 'Rmv.Filtered' and not filtered:
                        b.caption = 'Dur.Filter'
                        b.font = pygame.font.SysFont('courier', 16)
                        b._update()
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
                                    ellip = confidenceEllipse([(form.F1,form.F2) for form in vowList],1, DISPLAYSURFACE)
                                    stdDevCounter = 1
                                    b.caption = 'Std Dev 1'
                                    b.bgcolor = Color("darkolivegreen4")
                                elif stdDevCounter == 1:
                                    ellip = confidenceEllipse([(form.F1,form.F2) for form in vowList],2, DISPLAYSURFACE)
                                    stdDevCounter = 2
                                    b.caption = 'Std Dev 2'
                                elif stdDevCounter == 2:
                                    ellip = confidenceEllipse([(form.F1,form.F2) for form in vowList],3, DISPLAYSURFACE)
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
                                formType = 'num'
                                b.caption = 'RemeasureF'
                            elif b.caption == 'RemeasureF':
                                if os.path.isdir(args.p):
                                    praatMode = True
                                    b.caption = 'RemeasureP'
                                else: 
                                    formType = 'dur'
                                    b.caption = 'Remeasure%'
                            else:                        
                                praatMode = False
                                formType = 'dur'
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
                            vowelChange = True
                            while not minDur:    
                                minDur = inputbox.ask(DISPLAYSURFACE,'Minimum Duration (ms)')
                                try:                                    
                                    minDur = int(minDur)
                                    break
                                except: 
                                    if minDur != '':
                                        minDur = None
                                    else: break
                            if minDur == '': break
                            for v in vowList:
                                if int(v.duration) < minDur:
                                    filtered += [v]
                            b.caption = 'Rmv.Filtered'
                            b.font = pygame.font.SysFont('courier', 14) 
                        elif b.caption == 'Rmv.Filtered' and filtered:
                            yesno = None
                            while not yesno:
                                yesno = inputbox.ask(DISPLAYSURFACE,'Remove %r filtered vowels? y/n' % len(filtered)).strip().lower()
                                if yesno not in ['y','n']:
                                    if yesno == 'yes': minDur = 'y'
                                    elif yesno == 'no': minDur = 'n'
                                    else: yesno = None
                            vowelChange = True
                            if yesno == 'y':
                                for f in filtered:
                                    reason = 'filtered: below minimum duration of %d ms' % minDur
                                    outCode = codes[f.vowelCode] if inputType == 'plt' else arpCodes[f.vowelCode]
                                    newInfo = [str(wr) for wr in [f.id,outCode,f.word,'NA',f.time,f.duration,f.stress,f.maxForm,'NA','NA','NA','NA','removed: '+reason]]
                                    allLogs[f.wFile][f.time] = newInfo
                                    vowButtonList.remove(f)
                            filtered = []
                            minDur = None
                            vowelChange = True
                            b.caption = 'Dur.Filter'
                            b.font = pygame.font.SysFont('courier', 16)
                            b._update()

                        
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
                            vowButtonList = displayMemory.pop()
                            allLogs = copy.deepcopy(logMemory.pop())
                            if len(displayMemory) < 2: displayMemory = [[v for v in vowButtonList]]
                            if len(logMemory) <2: logMemory = [copy.deepcopy(allLogs)]
                            vowelChange = True
                        
                        if b.caption == 'Rmv. Bad':
                            b.caption = 'Rmv. OK'
                            b.bgcolor = Color('lightskyblue')
                            remReason = 'OK'
                        elif b.caption == 'Rmv. OK':
                            b.bgcolor = Color('red')
                            b.caption = 'Rmv. Bad'
                            remReason = ''

                        if b.caption == 'Zoom':
                            b.font.set_bold(False)
                            if b.bgcolor == Color('darkolivegreen2'):
                                zooming = True
                                b.bgcolor = Color('darkolivegreen4')
                                start, stop = (),()
                            else:
                                zooming = False
                                b.bgcolor = Color('darkolivegreen2')
                                start, stop = (),()
                        elif b.caption == 'Reset Zoom':
                            b.font.set_bold(False)
                            vowButtonList, currentVowel = resize((minF1,minF2,maxF1,maxF2), vowButtonList, currentVowel) 
                            #b.bgcolor = Color('darkolivegreen2')
                            b.caption = 'Zoom'
                            vowelChange = True
                        
                        if b.caption == 'Check Last':
                            if lastVowel: 
                                call(['open', args.p])
                                call(['support_scripts/sendpraat', '0', 'praat', 'execute \"'+os.path.join(os.getcwd(),'support_scripts/zoomIn.praat')+'\" \"' + lastVowel.wFile + '\" \"'+os.path.join(os.getcwd(),'praatLog')+ '\" ' + lastVowel.time + ' 0 ' + lastVowel.maxForm+'"'])

                        if b.caption == 'Resume' and b.bgcolor != Color('darkolivegreen4'):
                            displayMemory += [[v for v in vowButtonList]]
                            logMemory += [copy.deepcopy(allLogs)]
                            for v in vowButtonList:
                                if isinstance(v.alreadyCorrected,tuple):
                                    x,y = calculateVowelLocation((v.alreadyCorrected[2],v.alreadyCorrected[3])) 
                                    buttonRect = pygame.Rect(x,y, 8, 8)
                                    buttonRect.center = (x,y)
                                    button = pygbutton.PygButton(buttonRect, '►'.decode('utf8'),border = False) # make new button for each alternate formant
                                    button.bgcolor = WHITE # set colour of alternate formants to black
                                    button.fgcolor = v.button.bgcolor
                                    newV = v.makeAlternate(v.alreadyCorrected[2],v.alreadyCorrected[3],button)
                                    newV.time, newV.maxForm = v.alreadyCorrected[:2]
                                    newV.alreadyCorrected = None
                                    vowButtonList.remove(v)
                                    vowButtonList.append(newV)

                            vowButtonList = [v for v in vowButtonList if v.alreadyCorrected != 'removed']
                            b.bgcolor = Color('darkolivegreen4')
                            vowelChange = True


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
                        if b.caption in celDisplayed:
                            b.font.set_bold(False)
                            b._update()
                            celDisplayed.remove(b.caption)
                        else:
                            b.font.set_bold(True)
                            b._update()
                            celDisplayed += [b.caption]
                        textList = []
                        filtered = []
                        minDur = None
                        vowelChange = True
                

                if currentVowel:
                    if 'click' in currentVowel.button.handleEvent(event) and not pressCTRLA:
                        if pressed[K_SPACE]:
                            call(['open', args.p])
                            call(['support_scripts/sendpraat', '0', 'praat', 'execute \"'+os.path.join(os.getcwd(),'support_scripts/zoomIn.praat')+'\" \"' + currentVowel.wFile + '\" \"'+os.path.join(os.getcwd(),'praatLog')+ '\" ' + currentVowel.time + ' 0 ' + currentVowel.maxForm+'"'])
                        elif pressed[ctrl[0]] or pressed[ctrl[1]]:   
                            displayMemory += [[v for v in vowButtonList]]
                            logMemory += [copy.deepcopy(allLogs)]
                            vowelChange = True
                            reason = ''
                            if pressed[shft[0]] or pressed[shft[1]]:
                                while not reason or reason == 'QUITNOW':
                                    reason = inputbox.ask(DISPLAYSURFACE,'Reason ')
                            clear(currentVowel, reason)
                            vowButtonList.remove(currentVowel)
                            #vowList.remove(currentVowel)
                            currentVowel = None
                            textList = []


                        
                        else:
                            displayMemory += [[v for v in vowButtonList]]
                            logMemory += [copy.deepcopy(allLogs)]    
                            if praatMode:
                                message = 'runScript: \"support_scripts/zoomIn.praat\", %r, %r' % (currentVowel.wFile,float(currentVowel.time))
                                call(['open', args.p])
                                call(['support_scripts/sendpraat', '0', 'praat', 'execute \"'+os.path.join(os.getcwd(),'support_scripts/zoomIn.praat')+'\" \"' + currentVowel.wFile + '\" \"'+os.path.join(os.getcwd(),'praatLog')+ '\" ' + currentVowel.time + ' 1 '+currentVowel.maxForm+'"'])  
                                chooseFormants = True
                                break   
                            forms = currentVowel.numForms if formType == 'num' else currentVowel.durForms 
                            for i,xform in enumerate(forms): # figure out where to write the alternate formant buttons
                                x,y = calculateVowelLocation(xform)
                                buttonRect = pygame.Rect(x,y, 8, 8)
                                buttonRect.center = (x,y)
                                button = pygbutton.PygButton(buttonRect, '►'.decode('utf8'),border = False) # make new button for each alternate formant
                                button.bgcolor = BLACK # set colour of alternate formants to black
                                button.fgcolor = BLACK
                                alt = currentVowel.makeAlternate(xform[0],xform[1],button)
                                if inputType == 'txt':
                                    if formType == 'dur':
                                        alt.time = str(round(((float(alt.duration)/1000.0)*((i+1)*0.2))+float(alt.timeRange[0]),3))
                                    else:
                                        alt.maxForm = str(3+i)
                                xFormButtons += [alt]
                            x,y = calculateVowelLocation((currentVowel.F1,currentVowel.F2))
                            buttonRect = pygame.Rect(x,y, 10, 10)
                            buttonRect.center = (x,y)
                            button = pygbutton.PygButton(buttonRect, '◉'.decode('utf8'), border = False)
                            button.bgcolor = WHITE 
                            button.fgcolor = currentVowel.button.fgcolor
                            alt = currentVowel.makeAlternate(currentVowel.F1,currentVowel.F2, button)
                            xFormButtons += [alt]
                            chooseFormants = True

                if vowelChange:
                    vowList = []
                    if inputType == 'txt':
                        if vowelMode == 'intersect':
                            for v in vowButtonList:    
                                    if (arpCodes[v.vowelCode] in arpDisplayed) and (v.celex in celDisplayed):
                                        vowList += [v] if v not in filtered else []
                        else: 
                            for v in vowButtonList:    
                                    if (arpCodes[v.vowelCode] in arpDisplayed) or (v.celex in celDisplayed):
                                        vowList += [v] if  v not in filtered else []
                    else: 
                        for b in permButtons[0]:
                            for v in vowButtonList:
                                vowList += [v] if b.bgcolor == v.button.fgcolor and b.caption in arpDisplayed and v not in filtered else []
                for v in vowList: # deal with all vowels currently displayed on screen
                    if 'enter' in v.button.handleEvent(event):
                        #f,g = v[1],v[2]
                        # write the vowel information to the display bit (lower right of the screen)
                        vname = arpCodes[v.vowelCode].upper() if inputType == 'txt' else codes[v.vowelCode]
                        textList = ['vowel: '+vname,'F1: '+str(v.F1),
                                     'F2: '+str(v.F2),'stress: '+v.stress,
                                     'duration: '+str(v.duration)+' ms','word: '+v.word,
                                     'time: '+v.time]
                        currentVowel = v
                        if args.f0: textList += ['pitch: '+v.pitch]
                        if inputType == 'txt': 
                            textList.insert(1,'celex: '+v.celex)
                            textList.insert(-1,'environ: '+v.pPhone+' v '+v.fPhone)
                            textList.insert(-1,'max formants: '+v.maxForm)
                        if play: # play the vowel sound (if play mode is on), plays 25 milliseconds on either side of measurement point
                            call(['play',v.wFile,'trim',str(float(v.time)-0.1), '='+str(float(v.time)+0.1)])  
                

            else:
                if praatMode:
                    if not xFormButtons:
                        buttonRect = currentVowel.button.rect.inflate(1,1)
                        button = pygbutton.PygButton(buttonRect, '◉'.decode('utf8'), border = False)
                        button.bgcolor = WHITE
                        button.fgcolor = currentVowel.button.fgcolor 
                        alt = currentVowel.makeAlternate(currentVowel.F1, currentVowel.F2 ,button)
                        xFormButtons = [alt]
                    if os.path.isfile(praatLog):
                        praatInfo = [(p.split()[0].strip(), p.split()[1].strip() ,p.split()[2].strip(), p.split()[3].strip()) for p in open(praatLog,'rU').readlines()]
                        call(['rm',praatLog])
                    if praatInfo:
                        for p in praatInfo:
                            x,y = calculateVowelLocation((float(p[1]),float(p[2])))
                            #if p != praatInfo[-1]:
                            buttonRect = pygame.Rect(x,y, 8, 8)
                            buttonRect.center = (x,y)
                            button = pygbutton.PygButton(buttonRect, '►'.decode('utf8'), border = False)
                            button.bgcolor = BLACK
                            button.fgcolor = BLACK 
                            alt = currentVowel.makeAlternate(float(p[1]),float(p[2]),button)
                            alt.time = str(round(float(p[0]),3))
                            try: alt.pitch = p[3]
                            except: pass 
                            xFormButtons += [alt]
                        praatInfo = []



                for b in permButtons[1]:
                    if 'click' in b.handleEvent(event):
                        if 'Cancel'in b.caption:
                            xFormButtons = []
                            chooseFormants = False
                            call(['support_scripts/sendpraat', '0', 'praat', 'Quit'])
                            vowelChange = True
                            

                for x in xFormButtons: # choose new formant
                    if 'click' in x.button.handleEvent(event): # click on black or white button to set new vowel location 
                        for vb in vowButtonList:
                            if vb.button is x.origButton:
                                x.button.fgcolor = vb.button.bgcolor if vb.button.bgcolor != WHITE else vb.button.fgcolor
                                x.button.bgcolor = WHITE
                                if x.button.caption != '►'.decode('utf8'):
                                    x.button.caption = '►'.decode('utf8')
                                    b.rect = b.rect.inflate(-1,-1)
                                #redoSpecs = tuple([x[0][1][0],x[0][1][1],x[1][1][2]]) 
                                #tempvb = tuple([x[0][0],redoSpecs]+list(x[1][2:]))
                                vowButtonList.remove(vb)
                                vowButtonList.append(x)
                                vowList.remove(vb)
                                vowList.append(x)
                                currentVowel = x
                                call(['support_scripts/sendpraat', '0', 'praat', 'Quit'])
                                oldv = vb
                        # write the information of the changed vowel to the list (to write to the log file later)
                        outCode = codes[x.vowelCode] if inputType == 'plt' else arpCodes[x.vowelCode]
                        newInfo = [str(wr) for wr in [oldv.id, outCode,x.word,oldv.time,x.time,x.duration,x.stress,x.maxForm,oldv.F1,x.F1,oldv.F2,x.F2]]
                        allLogs[oldv.wFile][oldv.time] = newInfo
                        chooseFormants = False
                        xFormButtons = []
                        vname = arpCodes[x.vowelCode].upper() if inputType == 'txt' else codes[x.vowelCode]

                        textList = ['vowel: '+vname,'F1: '+str(x.F1),
                                     'F2: '+str(x.F2),'stress: '+x.stress,
                                     'duration: '+x.duration+' ms','word: '+x.word,
                                     'time: '+x.time]
                        if args.f0: textList += ['pitch: '+ x.pitch]
                        if inputType == 'txt': 
                            textList.insert(1,'celex: '+x.celex)
                            textList += ['environ.: '+x.pPhone+' v '+x.fPhone]
                            textList += ['max formants: '+x.maxForm]
                        praatInfo = []
                        lastVowel = currentVowel              
                        vowelChange = True
        
        for b in permButtons[1]:
            if b.caption in ['1','2','0']:
                if filtered: b.bgcolor = Color("darkolivegreen4")
                if b.bgcolor == Color("darkolivegreen2"):                            
                    stressFiltered += [b.caption]

            
        vowList = [v for v in vowList if v.stress not in stressFiltered]# and (v.F1 >= maxMin[0] and v.F1 <= maxMin[2] and v.F2 >= maxMin[1] and v.F2 <= maxMin[3])]
        stressFiltered = []
        if vowelChange:
            DISPLAYSURFACE.fill(windowBgColor)
        else: 
            for r in NOTPLOTRECTS:
                pygame.draw.rect(DISPLAYSURFACE,WHITE,r)
        
        if ellip and vowelChange: DISPLAYSURFACE.blit(ellip[0],ellip[1])
        pygame.draw.lines(DISPLAYSURFACE,BLACK,True, [(490,PLOTBOTTOM),(PLOTWIDTH,PLOTBOTTOM),(PLOTWIDTH,840),(490,840)],2) # draw rectangle to display vowel info
        pygame.draw.lines(DISPLAYSURFACE,BLACK,True, [(10,10),(PLOTWIDTH,10),(PLOTWIDTH,PLOTBOTTOM),(10,PLOTBOTTOM)],2) # draw rectangle to display vowel buttons
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
        

        
        for b in permDisplay: # draw vowels to screen
            b.draw(DISPLAYSURFACE)
        
        if textList:    # draw info for last vowel scrolled over to screen
            for i,t in enumerate(textList):
                label = textListFont.render(t, 1, BLACK)
                DISPLAYSURFACE.blit(label, (500, 605+(21*i)))
        
        if chooseFormants: # draw alternate formant buttons (when in choose formant mode)
            for xf in xFormButtons:
                xf.button.draw(DISPLAYSURFACE)
        
        if vowelChange:
            DISPLAYSURFACE.blit(F1,(PLOTWIDTH-myfont.size('F1')[0],PLOTBOTTOM/2))
            DISPLAYSURFACE.blit(F2,(PLOTWIDTH/2,10))
            drawGrid(numFont)
            for b in [v.button for v in vowList]:
                b.draw(DISPLAYSURFACE)
            vowelChange = False
            if zoomLines: pygame.draw.lines(DISPLAYSURFACE,BLACK,True,zoomLines,1)
        pygame.display.update() # update screen
        FPSCLOCK.tick(FPS) # screen updates at 30 frames per second


if __name__ == '__main__':
    main()