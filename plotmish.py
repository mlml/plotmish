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
from os.path import isdir, isfile, join, basename
from glob import glob
from subprocess import call, Popen
if isdir('plotmish'):
    os.chdir('plotmish')
sys.path.append('support_scripts')
import pygbutton, inputbox, mapToCelex
from pygame.locals import *
try: import numpy as np
except: print >> sys.stderr, 'ca'
#set path to epw.cd celex dict (currently in support scripts and called celex.cd)
mapToCelex.changeCelexPath('support_scripts/celex.cd')

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

#set window sizes and frames per second
FPS = 10
WINDOWWIDTH = 820
WINDOWHEIGHT = 850


#set fonts
myfont = pygame.font.SysFont('helvetica',20)    
numFont = pygame.font.SysFont('helvetica',15)
miniFont = pygame.font.SysFont('helvetica',12)
textListFont = pygame.font.SysFont('courier',18)
smallButtonFont = pygame.font.SysFont('courier', 16)

#pressed button lists
ctrl = [K_RCTRL, K_LCTRL] 
shft = [K_RSHIFT, K_LSHIFT]

# vowel token class
class vowel:
    def __init__(self, f1, f2, wfile):
        self.name = ''
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
        # makes identical version of vowel with different f1 and 
        # f2 and button
        newV = vowel(f1,f2, self.wFile)
        newV.name = self.name
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

# vowel plot class
class vowelPlot:
    def __init__(self, display):
        self.display = display
        self.textList = [] # list to write the info for the vowel that was scrolled over last
        self.xFormButtons = [] # list to write the alternate measurements to (when re-evaluating a vowel)
        self.currentVowel = None # current vowel button (last scrolled over)
        self.oldv = None # when remeasuring a vowel this stores the old values 
        self.ellip = [] # list to write ellipse variables (from output of confidenceEllipse())
        self.filtered = [] # list of vowels filtered by duration or orthography
        self.minDur = None # minimum duration of vowels to be displayed (None means minimum duration is 0)
        self.filtWrd = None # word to filter from the plot (None means display all vowels)
        self.stressFiltered = [] # stress markers not to display on plot (contains 1,2,0 only)
        self.firstSave = False # makes sure that saving changes more than once doesn't constantly rewrite the log files 
        self.arpDisplayed = [] # list of arpabet vowels to display on plot
        self.celDisplayed = [] # list of celex vowels to display on plot
        self.remReason = '' # vowel removal mode: either 'BAD' or 'OK'
        self.vowButtons = [] # list of all buttons that have not been removed
        self.height = 600 # height of the plot
        self.width = 700 # width of the plot
        self.maxF1 = None 
        self.minF1 = None
        self.maxF2 = None
        self.minF2 = None
        self.maxMin = () # tuple of (minF1, minF2, maxF1, maxF2) this changes according to zoom
        self.defaultMaxMin = () # default of self.maxMin (does not change when zooming)
        self.allLogs = {} # dictionary of all changes made since last save




#set default black and white colours
WHITE = (255, 255, 255, 0)
BLACK = (0, 0, 0)

# dictionary of all vowel codes and corresponding colours
colours =   {'AA': (127, 255, 212, 255),
             'AE': (216, 191, 216, 255),
             'AH': (124, 252, 0, 255),
             'AO': (255, 0, 0, 255),
             'AW': (107, 142, 35, 255),
             'AY': (60, 179, 113, 255),
             'EH': (255, 99, 71, 255),
             'ER': (124, 252, 0, 255),
             'EY': (139, 0, 139, 255),
             'IH': (139, 69, 19, 255),
             'IW': (139, 26, 26, 255),
             'IY': (238, 154, 0, 255),
             'OW': (0, 191, 255, 255),
             'OY': (65, 105, 225, 255),
             'UH': (255, 105, 180, 255),
             'UW': (120, 120, 120, 255)}

# cmu/arpabet vowels
arpVowels =  ('AA',  'IY',  'AE',  'EH',  'AH',  'UW',  'OY',  'AO',
              'UH', 'IH',  'OW',  'EY',  'IW',  'AW',  'AY',  'ER') 

def writeLogs(plot):
    # write to new log file or append to old one
    
    #only overwrite files if this is the first time writing this session
    if plot.firstSave: 
        append = True
    else:
        append = False
        plot.firstSave = True
    # write to -corrLog.csv files
    for f,writeThis in plot.allLogs.items():
        if not writeThis: continue
        # write header to log file
        header = True if not isfile(join(args.o,basename(f).replace('.wav','-corrLog.csv'))) else False
        if args.a or append:
            log = csv.writer(open(join(args.o,basename(f).replace('.wav','-corrLog.csv')),'a'))
            if header: log.writerow(['annotator','id','vowel','word','oldTime','time','duration (ms)','stress','maxForms','oldF1','F1','oldF2','F2'])
        else:
            log = csv.writer(open(join(args.o,basename(f).replace('.wav','-corrLog.csv')),'wb'))
            log.writerow(['annotator','id','vowel','word','oldTime','time','duration (ms)','stress','maxForms','oldF1','F1','oldF2','F2'])
        # write info to log file 
        for w in writeThis:
            log.writerow([args.annotator]+[w[0].split('-')[-1]]+w[1:])

# get pitch files if -f0 flag is used
if args.f0: pitchFiles = glob(join(args.f0,'*.Pitch'))

def getFiles():
    # get all relevant files and pair them together
    # as (wav file, formant.txt file)
    files = []
    # if looking in directories
    if isdir(args.wav) and isdir(args.vowels):
        wFiles = glob(join(args.wav,'*'+args.k+'*.wav'))
        vFiles = glob(join(args.vowels,'*'+args.k+'*'))
        vFiles = [v for v in vFiles if '.plt' in v or 'formant.txt' in v]
        for w in wFiles:
            for v in vFiles:
                if basename(w.replace('.wav','')) in basename(v):
                    files += [(w,v)]
    # if only one formant file given
    elif isdir(args.wav):
        wFiles = glob(join(args.wav,'*'+args.k+'*.wav'))
        for w in wFiles:
            if basename(w.replace('.wav','')) in basename(args.vowels):
                files += [(w,args.vowels)]
    # if only one wav file given
    elif isdir(args.vowels):
        vFiles = glob(join(args.vowels,'*'+args.k+'*'))
        for v in vFiles:
            if basename(args.wav.replace('.wav','')) in basename(v):
                files += [(args.wav,v)]
    # if only one formant file and only one wav file is given
    else:
        files += [(args.wav,args.vowels)]
    files = [f for f in files if 'txt' == f[1][-3:]]
    assert files, 'ERROR: no files found'
    return files

def calculateVowelLocation(f, plot):
    # calculates the location to display the vowel based on tuple of (F1,F2)    
    x = (((plot.maxMin[3]-float(f[1])))/(plot.maxMin[3]-plot.maxMin[1]))*(plot.width-20)+15 
    y = ((float(f[0]) - plot.maxMin[0])/(plot.maxMin[2]-plot.maxMin[0]))*(plot.height-20)+15
    return (x,y)

def makeVowelButton(v, plot):
    # makes a new vowel button for each new vowel
    x,y = calculateVowelLocation((v.F1,v.F2), plot)
    buttonRect = pygame.Rect(x,y, 8, 8)
    buttonRect.center = (x,y)
    button = pygbutton.PygButton(buttonRect,'►'.decode('utf8'),border = False)
    button.bgcolor = colours[v.name] 
    button.fgcolor = colours[v.name]
    return button

def getCelexVowel(word,cmu,vIndex):
    # gets celex vowel for each vowel token according to the 
    # word it occurs in (not a one to one mapping)
    allIndexes = [i for i,c in enumerate(cmu) if c[:-1] in arpVowels]
    vIndex = allIndexes.index(vIndex)
    try:
        celVowel = mapToCelex.mapToCelex(word,cmu)[vIndex][1][0]
    except: 
        celVowel = 'NA'
    return celVowel

# place to write last file and frame checked
# when iterating over the pitch files
oldPitchFile = None
oldPitchFrame = 0

def getPitch(pitchList, timestamp, thisPitch):
    # find pitch at time for a vowel token
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
                 

def assignMaxMin(plot, allvowels):
    # get maxMin value for plot
    for a in allvowels:
        plot.maxF1 = max([float(a.F1) for a in allvowels])
        plot.minF1 = min([float(a.F1) for a in allvowels])
        plot.maxF2 = max([float(a.F2) for a in allvowels])
        plot.minF2 = min([float(a.F2) for a in allvowels])
    plot.maxMin = (plot.minF1, plot.minF2, plot.maxF1, plot.maxF2)
    plot.defaultMaxMin = (plot.minF1, plot.minF2, plot.maxF1, plot.maxF2)

def getVowels(plot, files):
    # reads all the vowels from the formant.txt file
    allvowels = []
    for f in files:
        # display which file is being processed TODO: speed this up
        loadingMessage(plot.display, myfont, ['Loading Vowels', basename(f[0]).replace('.wav','')])
        # get pitch track if f0 is specified as an argument (from the command line)
        if args.f0: 
            thisPitch = [p for p in pitchFiles if basename(p).replace('.Pitch','') in basename(f[0])][0]
            pitchList = [p.replace('\n','').strip() for p in open(thisPitch,'rU').readlines()]
        vowelF = open(f[1],'r')
        vowels = vowelF.readlines()[3:]
        #get associated log file if available
        try:
            logF = open(join(args.o , basename(f[0]).replace('.wav','')+'-corrLog.csv'),'rU')
            logR = list(csv.reader(logF))[1:]
            logF.close()
        except: 
            logR = None    

        for i,v in enumerate(vowels):
            v = v.split('\t')
            nV = vowel(float(v[3]),float(v[4]),f[0]) # initialize new vowel
            # get other formant measurements from various points in the vowel duration  
            # (F1@20%, F2@20%, F1@35%, F2@35%, F1@50%, F2@50%, F1@65%, F2@65%, F1@80%, F2@80%)
            nV.id = basename(f[0]).replace('.wav','')+'-'+str(i+1)
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
            # get other values 
            cmuPron = [p.strip() for p in re.sub('[\[\]\']','',v[33]).split(',')]
            nV.pPhone = v[31]
            nV.fPhone = v[32]
            nV.word = v[2]
            vIndex = int(v[34])
            nV.celex = getCelexVowel(nV.word,cmuPron,vIndex)
            nV.time = v[9]
            if args.f0: nV.pitch = getPitch(pitchList,timestamp, thisPitch) 
            nV.maxForm = v[35]
            nV.name = v[0]
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
            allvowels += [nV]
    
    assignMaxMin(plot, allvowels)

    for av in allvowels:
        av.button = makeVowelButton(av, plot)
    return allvowels


def confidenceEllipse(xyPoints,sdev,plot):
    # make a confidence ellipse of the points currently plotted on the scree
    # adapted from Jaime at: 
    #stackoverflow.com/questions/20126061/creating-a-confidence-ellipses-in-a-sccatterplot-using-matplotlib
    x = [calculateVowelLocation(xy, plot)[0] for xy in xyPoints]
    y = [calculateVowelLocation(xy, plot)[1] for xy in xyPoints]
    angleAdjust = False if np.mean([p[1] for p in sorted(xyPoints)[:int(len(xyPoints)/2.0)]]) < np.mean([p[1] for p in sorted(xyPoints)[int(len(xyPoints)/2.0):]]) else True
    mean = (np.mean(x),np.mean(y))
    cov = np.cov(x, y)
    lambda_, v = np.linalg.eig(cov)
    lambda_ = np.sqrt(lambda_)
    angle = np.rad2deg(np.arccos(v[0, 0]))
    if angleAdjust: angle = 180-angle
    width=lambda_[0]*sdev*2
    height=lambda_[1]*sdev*2
    plot.display.fill(WHITE)
    ellipDim = pygame.Rect(0,0,width,height)
    ellipDim.center = (WINDOWWIDTH/2.0,WINDOWHEIGHT/2.0)
    pygame.draw.ellipse(plot.display,BLACK,ellipDim,2)
    rot_img = pygame.transform.rotate(plot.display, angle)
    img_rect = rot_img.get_rect()
    img_rect.center = mean
    plot.ellip = (rot_img, img_rect)


def makeButtons():
    # make permanent buttons (on the bottom of the screen)
    vowButtons = []
    onOffButtons = []
    celexButtons = []
    #arpabet vowels
    # front
    for i,c in enumerate(['IY', 'IH', 'EY', 'EH', 'AE']):
        button = pygbutton.PygButton((20, 640+(i*35), 30, 30), c)
        button.bgcolor = colours[c]
        vowButtons.append(button)
    # central
    button = pygbutton.PygButton((60, 710, 30, 30), 'AH')
    button.bgcolor = colours['AH']
    vowButtons.append(button)
    # back
    for i,c in enumerate(['UW', 'UH', 'OW', 'AO', 'AA']):
        button = pygbutton.PygButton((100, 640+(i*35), 30, 30), c)
        button.bgcolor = colours[c]
        vowButtons.append(button)
    # diphthongs and rhoticized
    for i,c in enumerate(['AY','OY', 'OW', 'IW', 'ER']):
        button = pygbutton.PygButton((140, 640+(i*35), 30, 30), c)
        button.bgcolor = colours[c]
        vowButtons.append(button)
    # celex vowels
    # front
    for i,c in enumerate(['i','I','1','E','{']):
        button = pygbutton.PygButton((255, 640+(i*40), 30, 30), c)
        button.bgcolor = Color("lightskyblue")
        celexButtons.append(button)
    # central
    for i,c in enumerate(['@','3','V','Q']):
        button = pygbutton.PygButton((295, 640+(i*40), 30, 30), c)
        button.bgcolor = Color("lightskyblue")
        celexButtons.append(button)
    # back
    for i,c in enumerate(['u','U','5','$','#']):
        button = pygbutton.PygButton((335, 640+(i*40), 30, 30), c)
        button.bgcolor = Color("lightskyblue")
        celexButtons.append(button)
    #diphthongs
    for i,c in enumerate(['2','4','6']):
        button = pygbutton.PygButton((375, 640+(i*40), 30, 30), c)
        button.bgcolor = Color("lightgreen")
        celexButtons.append(button)
    for i,c in enumerate(['7','8','9','H','P']):
        button = pygbutton.PygButton((415, 640+(i*40), 30, 30), c)
        button.bgcolor = Color("lightgreen")
        celexButtons.append(button)
    # union/intersect button
    button = pygbutton.PygButton((190,720,30,30),'U'.decode('utf8'))
    button.bgcolor = Color('darkolivegreen2')
    button.font = myfont
    onOffButtons.append(button)
    # side buttons    
    sideButtons = ['Show All', 'Clear', 'Play', 'Std Dev', 'Dur.Filter','Wrd.Filter', 'Zoom','RemeasureP',
                    'Cancel', 'Saved', 'Undo', 'Check Last', 'Rmv. Bad', 'Resume'] 
    lowest = 0
    for i,c in enumerate(sideButtons):
        button = pygbutton.PygButton((705, 10+(i*40), 110, 30), c)
        lowest = 10+(i*40)+40
        if button.caption == 'Rmv. Bad': button.bgcolor = Color('red')
        else: button.bgcolor = Color('darkolivegreen2')
        onOffButtons.append(button)    
    #stress buttons
    for i,c in enumerate(['1','2','0']):
        button = pygbutton.PygButton((705+(i*37),lowest, 35, 30), c)
        button.bgcolor = Color('darkolivegreen4')
        onOffButtons.append(button)      

    return (vowButtons,onOffButtons,celexButtons)

def loadingMessage(surface, font, message):
    # display loading message
    surface.fill(WHITE)
    for i,m in enumerate(message):
        mess = font.render(m,1,BLACK)
        surface.blit(mess,(WINDOWWIDTH/2.0-(font.size(m)[0]/2.0),WINDOWHEIGHT/2.0-(font.size(m)[1]/2.0)+(i*(font.size(m)[1])+5)))
    pygame.display.update()

def drawGrid(numFont, plot):
    # draw grid and max/min over plot area
    # horizontal lines are every 100 Hz
    # vertical lines are every 50 Hz 
    
    # initialize start and end points and the distance between lines
    intervalH = int(((plot.height-10)/(plot.maxF1-plot.minF1))*50)
    startH = int(((plot.height-10)/(plot.maxF1-plot.minF1))*(math.ceil(plot.minF1/50.0)*50 - plot.minF1)+10)
    startV = WINDOWWIDTH - int(((plot.width-10)/(plot.maxF2-plot.minF2))*(math.ceil(plot.minF2/100.0)*100 - plot.minF2) + (WINDOWWIDTH-plot.width))
    intervalV = int(((plot.width-10)/(plot.maxF2-plot.minF2))*100)
    h,v = (0,0)
    # draw horizontal lines
    while True:
        hlimit = startH + h*intervalH
        if hlimit > plot.height: break
        pygame.draw.line(plot.display,Color('grey87') ,(10,hlimit),(plot.width,hlimit)) 
        h += 1
    # draw vertical lines
    while True:
        vlimit = startV - v*intervalV
        if vlimit < 10: break
        pygame.draw.line(plot.display,Color('grey87'),(vlimit,plot.height),(vlimit, 10))
        v += 1
    # write max and min values for F1 and F2 
    fontMaxMin = [numFont.render(str(int(i)),1,BLACK) for i in plot.maxMin]
    plot.display.blit(fontMaxMin[0],(plot.width-numFont.size(str(int(plot.minF1)))[0],numFont.size(str(int(plot.minF1)))[1]+10))
    plot.display.blit(fontMaxMin[1],(plot.width-numFont.size(str(int(plot.minF2)))[0]-10,10))
    plot.display.blit(fontMaxMin[2],(plot.width-numFont.size(str(int(plot.maxF1)))[0], plot.height-numFont.size(str(int(plot.minF1)))[1]))
    plot.display.blit(fontMaxMin[3],(12, 10))


def resize(tempMaxMin, plot):
    # recalculate the location of all vowels when zooming
    if tempMaxMin != plot.defaultMaxMin:
        temp = [None,None,None,None]
        temp[0] = (plot.maxF1-plot.minF1)*(tempMaxMin[0]/float(plot.height-10))+plot.minF1
        temp[1] = plot.maxF2-((plot.maxF2-plot.minF2)*(tempMaxMin[1]/float(plot.width-10)))
        temp[2] = (plot.maxF1-plot.minF1)*(tempMaxMin[2]/float(plot.height-10))+plot.minF1
        temp[3] = plot.maxF2-((plot.maxF2-plot.minF2)*(tempMaxMin[3]/float(plot.width-10)))    
        plot.maxMin = tuple(temp)
        plot.minF1, plot.minF2, plot.maxF1, plot.maxF2 = temp
    else: 
        plot.maxMin = plot.defaultMaxMin
        plot.minF1, plot.minF2, plot.maxF1, plot.maxF2 = plot.defaultMaxMin
    # set the vowel buttons to their new location
    for v in plot.vowButtons:
        x,y = calculateVowelLocation((v.F1,v.F2),plot)
        v.button.rect.center = (x,y)
    # set the current vowel to it's new location
    if plot.currentVowel:
        x,y = calculateVowelLocation((plot.currentVowel.F1, plot.currentVowel.F2), plot)
        plot.currentVowel.button.rect.center = (x,y)

def clearRange(tempMaxMin, reason, plot, within = None):
    # clear a range of vowels that fall in tempMaxMin
    # with a reason for their removal
    # only remove vowels in the within list (this is used to only remove vowels currently
    #  displayed on the screen, not all vowels in the range)
    if not within: within = plot.vowButtons # remove all vowels in range if within not set
    # clear the vowel if it's in the range
    tempVBL = []
    for v in plot.vowButtons:
        x,y = v.button.rect.center
        if not (y > tempMaxMin[0] and x < tempMaxMin[1] and y < tempMaxMin[2] and x > tempMaxMin[3]) or v not in within:
            tempVBL += [v]
        else:
            clear(v, reason, plot)
    # remove current vowel if it falls in the range
    if plot.currentVowel:
        x,y = plot.currentVowel.button.rect.center
        plot.currentVowel = plot.currentVowel if not (y > tempMaxMin[0] and x < tempMaxMin[1] and y < tempMaxMin[2] and x > tempMaxMin[3]) else None 
    if not plot.currentVowel: plot.textList = [] # if the current vowel is removed, stop displaying it's info
    plot.vowButtons = tempVBL

def clear(vowel, reason, plot):
    # write to log that a vowel has been removed with a given reason
    because = 'unallowed variant' if not plot.remReason and not reason else plot.remReason+' '+reason
    because = 'removed: '+because if not plot.remReason else because
    newInfo = [str(wr) for wr in [vowel.id, vowel.name ,vowel.word,'NA',vowel.time,vowel.duration,vowel.stress,vowel.maxForm,'NA','NA','NA','NA',because]]
    plot.allLogs[vowel.wFile] += [newInfo]


def updateDisplayed(displayed, button, plot):
    # return the list of vowels to display 
    # according to the arp or celex vowel
    # they represent
    if button.caption in displayed:
        button.font.set_bold(False)
        button._update()
        displayed.remove(button.caption)
    else:
        button.font.set_bold(True)
        button._update()
        displayed += [button.caption]
    plot.textList = []
    plot.filtered = []
    plot.minDur = None
    plot.filtWrd = None
    return displayed

def writeInfo(v, plot):
    # update textlist to write to the info square (lower right)
    plot.textList = ['vowel: '+v.name,'celex: '+v.celex,'F1: '+str(v.F1),
             'F2: '+str(v.F2),'stress: '+v.stress,
             'duration: '+v.duration+' ms','word: '+v.word,
             'time: '+v.time,'environ.: '+v.pPhone+' v '+v.fPhone,
             'max formants: '+v.maxForm]
    if args.f0: plot.textList += ['pitch: '+ v.pitch]

def main():
    # this is where the magic happens
    global FPS 
    #initialize pygame surfaces and clocks
    pygame.init()    
    FPSCLOCK = pygame.time.Clock()       
    DISPLAYSURFACE = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT)) # create window according to dimensions
    plot = vowelPlot(DISPLAYSURFACE)
    NOTPLOTRECTS = (pygame.Rect(plot.width,0,WINDOWWIDTH - plot.width, plot.height),
                pygame.Rect(0,plot.height,WINDOWWIDTH,WINDOWHEIGHT - plot.height)) 
    caption = 'Plotmish - '+args.k if args.k else 'Plotmish'
    pygame.display.set_caption(caption) # set window caption
    #get info from all formant.txt files
    files = getFiles()
    #get all vowels in files 
    # make dictionary to log changes to   
    plot.allLogs = {f[0]:[] for f in files} 
    # make rendered text objects to draw on screen
    F1,F2 = (myfont.render('F1',1,Color('grey87')),myfont.render('F2',1,Color('grey87')))
    arpLabel = myfont.render('ARPABET',1,BLACK)
    celLabel = myfont.render('CELEX',1,BLACK)
    #initialize all buttons (permanent and vowel tokens)
    permButtons = makeButtons() # make permanent buttons (vowel buttons, display all/none buttons)
    permDisplay = permButtons[0]+permButtons[1]+permButtons[2] #put all permanent buttons in a list so they can be displayed
    plot.vowButtons = getVowels(plot, files)
    vowList = [] # list to write vowel that are currently displayed
    # set memory lists
    displayMemory = [plot.vowButtons] # list of all vowel plots up to the last save
    logMemory = [plot.allLogs] # list of all log dicts up to the last save
    praatLog = join(os.getcwd(),'praatLog') # set path of praatlog file (location of output of praat) 
    call(['rm', praatLog]) # remove praatlog if it exists (it shouldn't but just in case)
    # set variables for drawing lines when zooming or removing a range of buttons
    start, stop = (),() # tuples of the corners of the section of the plot to zoom in on (or remove buttons from)
    zoomLines = None # lines to draw when zooming or removing a group of buttons
    # set default behaviours
    vowelChange = True # set to True to change the vowel plot (necessary for continuous running with large numbers of vowels)
    play = False # indicates whether play button in on or off
    zooming = False # whether zoom button is on or off (and zoom mode is on)
    stdDevCounter = 0 #counter for drawing different ellipse sizes
    formType = 'dur' # remeasure mode (either 'dur' or 'num')
    praatMode = True # true if remeasure mode is praat (button caption is remeasureP)
    vowelMode = 'union' # vowel display mode: union or intersect of vowels in arpDisplayed and celDisplayed
    chooseFormants = False  # True if you are re-evaluating formant measurements 
    praatInfo = [] # list to write info from praatlog
    lastVowel = None # last vowel measured (for used with "check last" button)

    while True: # main loop
        ## this is the exciting bit
        for event in pygame.event.get(): # event handling loop
            ## process when quitting the program (hit escape to quit)
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                call(['rm', praatLog]) # sanity check to remove praat log (if it still exists)
                pygame.quit() 
                sys.exit()            
            # deal with zooming and selecting a range of vowels
            pressed = pygame.key.get_pressed() # get all buttons currently pressed
            pressCTRLA = (pressed[ctrl[0]] or pressed[ctrl[1]]) and pressed[K_a] #boolean indicating if ctrl+a is pressed (for selecting a range) 
            if zooming or pressCTRLA:
                T,L,B,R = None,None,None,None # Top, Left, Bottom, Right of the section of the plot you are selecting
                if event.type == MOUSEBUTTONDOWN: # click down to start selecting a section of the plot
                    start = pygame.mouse.get_pos()
                    FPS = 50 # increase frames per second for smooth drawing of selection box (temporary)
                elif start: 
                    stop = pygame.mouse.get_pos() # get current position of mouse 
                    L,R = (start[0],stop[0]) if start[0] < stop[0] else (stop[0],start[0]) # get dimensions of rectangle currently selected
                    T,B = (start[1],stop[1]) if start[1] < stop[1] else (stop[1],start[1])
                    zoomLines = [(L,T),(R,T),(R,B),(L,B)] # define dimensions of lines to draw (showing selection)
                    vowelChange = True                    
                    if event.type == MOUSEBUTTONUP: # when you're finally done with the clicking and the dragging
                        if not (L < 10 or R > plot.width or T < 10 or B > plot.height or T == B or L == R): # make sure you haven't selected outside the plot
                            FPS = 10 # resume normal frame rate
                            if pressCTRLA: # if removing a selection
                                reason = '' 
                                if (pressed[shft[0]] or pressed[shft[1]]): # get a reason for the removal if shift is pressed
                                    reason = inputbox.ask(plot.display,'Reason ')
                                    if not reason:
                                        vowelChange = True 
                                        zoomLines = None #stop drawing lines
                                        start, stop = (),() # reset start and stop tuples to default
                                        break # if no reason is given then don't remove the tokens
                                displayMemory += [[v for v in plot.vowButtons]] # make backup of display 
                                logMemory += [copy.deepcopy(plot.allLogs)] # make backup of log
                                clearRange((T,R,B,L), reason, plot, within = vowList) # clear all vowels currently displayed to screen in selected area
                                textList = []
                            else: # if zooming in 
                                resize((T,R,B,L), plot) # zoom in to to selected area
                                for b in permButtons[1]: # set zoom button caption 
                                    if b.caption == 'Zoom':
                                        b.caption = 'Reset Zoom'
                        zoomLines = None
                        start, stop = (),()
            elif zoomLines: 
                zoomLines = None
                start, stop = (),()
                vowelChange = True
            # if clicking buttons...
            if not chooseFormants:  # before you have selected a vowel for remeasurement  
                for b in permButtons[0]: # click a button with an arpabet code to display it on the screen 
                    if 'click' in b.handleEvent(event):
                        plot.arpDisplayed = updateDisplayed(plot.arpDisplayed, b, plot)
                        vowelChange = True


                for b in permButtons[2]: # click a button with a celex code to display it on the screen 
                    if 'click' in b.handleEvent(event):
                        plot.celDisplayed = updateDisplayed(plot.celDisplayed, b, plot)
                        vowelChange = True

                for b in permButtons[1]: # deal with buttons on right side of the screen
                    if b.font.get_bold(): b.font.set_bold(False) # makes sure button isn't bolded (happens for some reason ?)
                    # button says 'Saved' if all changes have been saved and 'Save' otherwise
                    if 'Saved' in b.caption and plot.allLogs != {f[0]:[] for f in files}:
                        b.caption = 'Save'
                        vowelChange = True
                    # button says Rmv if there are filtered tokens (can't filter by both word and duration at the same time)
                    if (b.caption == 'Rmv.Dur.Filt' or b.caption == 'Rmv.Wrd.Filt') and not plot.filtered:
                        b.caption = 'Dur.Filter' if b.caption == 'Rmv.Dur.Filt' else 'Wrd.Filter'
                        b.font = smallButtonFont
                        b._update()
                    # deal with buttons if they're clicked
                    if 'click' in b.handleEvent(event):
                        if b.caption == 'Show All': # show all tokens on the screen 
                            for b in permButtons[0]+permButtons[2]:
                                b.font.set_bold(True)
                                b._update()
                            vowList = plot.vowButtons
                            plot.arpDisplayed = [b.caption for b in permButtons[0]]
                            plot.celDisplayed = [b.caption for b in permButtons[2]]+['NA']
                            plot.filtered = []
                            plot.minDur = None
                            plot.filtWrd = None
                            vowelChange = True
                        if b.caption == 'Clear': # show no buttons on the screen 
                            for b in permButtons[0]+permButtons[2]:
                                b.font.set_bold(False)
                                b._update()
                            plot.arpDisplayed = []
                            plot.celDisplayed = []
                            vowList = []
                            plot.textList = []
                            plot.filtered = []
                            plot.minDur = None
                            plot.filtWrd = None
                            vowelChange = True
                        if b.caption == 'Play': # start/stop play mode
                            if not play: 
                                play = True
                                FPS = 30 # increase frames per second so that the vowel you're currently on is played
                                b.bgcolor = Color("darkolivegreen4")
                            else: 
                                play = False 
                                FPS = 10 # resume regular frame rate
                                b.bgcolor = Color("darkolivegreen2")
                        if 'Std Dev' in b.caption: # draw ellipses based on 1-3 standard deviations from the mean (will not work if numpy not found)
                            try:
                                if stdDevCounter == 0:
                                    confidenceEllipse([(form.F1,form.F2) for form in vowList],1, plot)
                                    stdDevCounter = 1
                                    b.caption = 'Std Dev 1'
                                    b.bgcolor = Color("darkolivegreen4")
                                elif stdDevCounter == 1:
                                    confidenceEllipse([(form.F1,form.F2) for form in vowList],2, plot)
                                    stdDevCounter = 2
                                    b.caption = 'Std Dev 2'
                                elif stdDevCounter == 2:
                                    confidenceEllipse([(form.F1,form.F2) for form in vowList],3, plot)
                                    stdDevCounter = 3
                                    b.caption = 'Std Dev 3'
                                
                                else:
                                    plot.ellip = []
                                    b.caption = 'Std Dev'
                                    b.bgcolor = Color("darkolivegreen2")
                                    stdDevCounter = 0
                            except:
                                plot.ellip = []
                                b.caption = 'Std Dev'
                                b.bgcolor = Color("darkolivegreen2")
                                stdDevCounter = 0
                            vowelChange = True
                        if 'Remeasure' in b.caption: # change remeasurement mode (praat, %duration, max formants)
                            if b.caption == 'Remeasure%':
                                formType = 'num'
                                b.caption = 'RemeasureF'
                            elif b.caption == 'RemeasureF':
                                praatMode = True
                                b.caption = 'RemeasureP'
                            else:                        
                                praatMode = False
                                formType = 'dur'
                                b.caption = 'Remeasure%'
                        
                        if b.caption == 'Cancel' and praatMode: #quit praat if currently remeasuring using praat
                            call(['support_scripts/sendpraat', '0', 'praat', 'Quit'])

                        if b.caption == 'Dur.Filter' and not plot.filtered: # remove vowels based on minimum duration
                            plot.minDur = None
                            vowelChange = True
                            while not plot.minDur:    # ask user to input a minimum duration in a textbox on screen
                                plot.minDur = inputbox.ask(plot.display,'Minimum Duration (ms)') 
                                try:                                    
                                    plot.minDur = int(plot.minDur)
                                    break
                                except: 
                                    if plot.minDur != '':
                                        plot.minDur = None
                                    else: break
                            for v in vowList: # add vowels to a filtered list (not displayed but not removed yet)
                                if int(v.duration) < plot.minDur:
                                    plot.filtered += [v]
                            if plot.minDur == '' or not plot.filtered: # don't filter anything if no minimum duration is given
                                break
                            if plot.filtered: # change button caption 
                                b.caption = 'Rmv.Dur.Filt'
                                b.font = pygame.font.SysFont('courier', 14) 
                        elif b.caption == 'Rmv.Dur.Filt' and plot.filtered: # remove all filtered vowels
                            yesno = None
                            while not yesno: # double check they actually want to remove the vowels
                                yesno = inputbox.ask(plot.display,'Remove %r filtered vowels? y/n' % len(plot.filtered)).strip().lower()
                                if yesno not in ['y','n']:
                                    if yesno == 'yes': plot.minDur = 'y'
                                    elif yesno == 'no': plot.minDur = 'n'
                                    else: yesno = None
                            vowelChange = True
                            if yesno == 'y': # if yes, remove all the vowels in filtered
                                displayMemory += [[v for v in plot.vowButtons]]
                                logMemory += [copy.deepcopy(plot.allLogs)]
                                for f in plot.filtered:
                                    reason = 'filtered: below minimum duration of %d ms' % plot.minDur
                                    clear(f,reason, plot)
                                    plot.vowButtons.remove(f) 
                            # reset buttons and appropriate lists
                            plot.filtered = []
                            plot.minDur = None
                            vowelChange = True
                            b.caption = 'Dur.Filter'
                            b.font = smallButtonFont
                            b._update()

                        
                        if b.caption in ['1','2','0']: # change stress button colours according to what should be displayed
                            if b.bgcolor == Color("darkolivegreen4"): b.bgcolor = Color("darkolivegreen2")
                            else: b.bgcolor = Color("darkolivegreen4") 
                            vowelChange = True
                        
                        if 'Save' in b.caption: # save all changes to -corrLog.csv files
                            writeLogs(plot)
                            plot.allLogs = {f[0]:[] for f in files}
                            b.caption = 'Saved'
                            vowelChange = True
                            displayMemory = [[v for v in plot.vowButtons]]
                        
                        if 'U'.decode('utf8') == b.caption: # change from union to intersect mode (for arp and celex vowels)
                            vowelMode = 'intersect'
                            b.caption = '∩'.decode('utf8')
                            vowelChange = True
                        elif '∩'.decode('utf8') == b.caption: # change from intersect to union mode (for arp and celex vowels)
                            vowelMode = 'union'
                            b.caption = 'U'.decode('utf8')
                            vowelChange = True
 
                        if b.caption == 'Undo': # undo previous change by restoring the last entry in displayMemory and logMemory
                            plot.vowButtons = displayMemory.pop()
                            plot.allLogs = copy.deepcopy(logMemory.pop())
                            if len(displayMemory) < 2: displayMemory = [[v for v in plot.vowButtons]]
                            if len(logMemory) <2: logMemory = [copy.deepcopy(plot.allLogs)]
                            vowelChange = True
                        
                        if b.caption == 'Rmv. Bad': # change the reason to remove a vowel (because it's bad or because its been checked and is ok)
                            b.caption = 'Rmv. OK'
                            b.bgcolor = Color('lightskyblue')
                            plot.remReason = 'OK'
                        elif b.caption == 'Rmv. OK':
                            b.bgcolor = Color('red')
                            b.caption = 'Rmv. Bad'
                            plot.remReason = ''

                        if b.caption == 'Zoom': # start zoom mode (clicking and dragging on the plot will now zoom in to that region)
                            if b.bgcolor == Color('darkolivegreen2'):
                                zooming = True
                                b.bgcolor = Color('darkolivegreen4')
                                start, stop = (),()
                            else:
                                zooming = False
                                b.bgcolor = Color('darkolivegreen2')
                                start, stop = (),()
                        elif b.caption == 'Reset Zoom': # reset zoom so all vowels are displayed
                            resize(plot.defaultMaxMin, plot) 
                            b.caption = 'Zoom'
                            vowelChange = True
                        
                        if b.caption == 'Check Last': # open praat to the last vowel measured (does not allow remeasuring)
                            if lastVowel: 
                                call(['open', args.p])
                                call(['support_scripts/sendpraat', '0', 'praat', 'execute \"'+join(os.getcwd(),'support_scripts/zoomIn.praat')+'\" \"' + lastVowel.wFile + '\" \"'+join(os.getcwd(),'praatLog')+ '\" ' + lastVowel.time + ' 0 ' + lastVowel.maxForm+'"'])

                        if b.caption == 'Resume' and b.bgcolor != Color('darkolivegreen4'): # set vowels on the screen according to remeasurements in the log files
                            displayMemory += [[v for v in plot.vowButtons]]
                            logMemory += [copy.deepcopy(plot.allLogs)]
                            for v in plot.vowButtons: 
                                if isinstance(v.alreadyCorrected,tuple): # change vowel if it's been changed and logged in the log file
                                    x,y = calculateVowelLocation((v.alreadyCorrected[2],v.alreadyCorrected[3]), plot) 
                                    buttonRect = pygame.Rect(x,y, 8, 8)
                                    buttonRect.center = (x,y)
                                    button = pygbutton.PygButton(buttonRect, '►'.decode('utf8'),border = False) 
                                    button.bgcolor = WHITE 
                                    button.fgcolor = v.button.bgcolor
                                    newV = v.makeAlternate(v.alreadyCorrected[2],v.alreadyCorrected[3],button) # make new vowel
                                    newV.time, newV.maxForm = v.alreadyCorrected[:2] # update maxforms and time 
                                    newV.alreadyCorrected = None 
                                    plot.vowButtons.remove(v) 
                                    plot.vowButtons.append(newV)

                            plot.vowButtons = [v for v in plot.vowButtons if v.alreadyCorrected != 'removed'] # remove vowel if it's been removed in the log file
                            b.bgcolor = Color('darkolivegreen4') 
                            vowelChange = True

                        if b.caption == 'Wrd.Filter' and not plot.filtered: # remove all vowels of a certain orthography (same as dur filter)
                            plot.filtWrd = inputbox.ask(plot.display,'Remove word').strip().upper() # ask user to input word to remove
                            for v in vowList:
                                if v.word == plot.filtWrd:
                                    plot.filtered += [v]
                            if not plot.filtWrd or not plot.filtered: # if a word isn't entered or there are no vowels that occur in that word, break
                                vowelChange = True
                                break
                            if plot.filtered: 
                                b.caption = 'Rmv.Wrd.Filt'
                                b.font = pygame.font.SysFont('courier', 14) 
                                vowelChange = True
                        elif b.caption == 'Rmv.Wrd.Filt' and plot.filtered: # remove all filtered vowels (by word)
                            yesno = None
                            while not yesno: # double check they want them removed
                                yesno = inputbox.ask(plot.display,'Remove %r filtered vowels? y/n' % len(plot.filtered)).strip().lower()
                                if yesno not in ['y','n']:
                                    if yesno.lower().strip() == 'yes': yesno = 'y'
                                    elif yesno.lower().strip() == 'no': yesno = 'n'
                            vowelChange = True
                            if yesno == 'y': # if yes then remove all filtered vowels
                                displayMemory += [[v for v in plot.vowButtons]]
                                logMemory += [copy.deepcopy(plot.allLogs)]
                                for f in plot.filtered:
                                    reason = 'filtered: word %r' % plot.filtWrd
                                    clear(f,reason,plot)
                                    plot.vowButtons.remove(f) 
                            # reset buttons and appropriate lists
                            plot.filtered = []
                            plot.filtWrd = None
                            vowelChange = True
                            b.caption = 'Wrd.Filter'
                            b.font = smallButtonFont
                            b._update()

                if plot.currentVowel and 'click' in plot.currentVowel.button.handleEvent(event) and not pressCTRLA: # if a vowel button is clicked
                    if pressed[ctrl[0]] or pressed[ctrl[1]]:   # hold control to remove the vowel
                        reason = ''
                        if pressed[shft[0]] or pressed[shft[1]]: # hold shift as well to add a comment before removing
                            reason = inputbox.ask(DISPLAYSURFACE,'Reason ')
                            if not reason: 
                                vowelChange = True
                                break
                        # reset buttons and appropriate lists and update memory
                        displayMemory += [[v for v in plot.vowButtons]]
                        logMemory += [copy.deepcopy(plot.allLogs)]
                        vowelChange = True
                        clear(plot.currentVowel, reason, plot)
                        plot.vowButtons.remove(plot.currentVowel) 
                        plot.currentVowel = None
                        textList = []

                    else: # remeasure vowel 
                        displayMemory += [[v for v in plot.vowButtons]] # update memory
                        logMemory += [copy.deepcopy(plot.allLogs)]    
                        if praatMode: # remeasure using praat (start by opening praat and going to appropriate location)
                            call(['rm', praatLog])
                            message = 'runScript: \"support_scripts/zoomIn.praat\", %r, %r' % (plot.currentVowel.wFile,float(plot.currentVowel.time))
                            call(['open', args.p])
                            call(['support_scripts/sendpraat', '0', 'praat', 'execute \"'+join(os.getcwd(),'support_scripts/zoomIn.praat')+'\" \"' + plot.currentVowel.wFile + '\" \"'+join(os.getcwd(),'praatLog')+ '\" ' + plot.currentVowel.time + ' 1 '+plot.currentVowel.maxForm+'"'])  
                            chooseFormants = True
                            break   
                        forms = plot.currentVowel.numForms if formType == 'num' else plot.currentVowel.durForms # use either duration or maxform alternate 
                        for i,xform in enumerate(forms): # figure out where to write the alternate formant buttons (black buttons)
                            x,y = calculateVowelLocation(xform, plot)
                            buttonRect = pygame.Rect(x,y, 8, 8)
                            buttonRect.center = (x,y)
                            button = pygbutton.PygButton(buttonRect, '►'.decode('utf8'),border = False) # make new button for each alternate formant
                            button.bgcolor = BLACK # set colour of alternate formants to black
                            button.fgcolor = BLACK
                            alt = plot.currentVowel.makeAlternate(xform[0],xform[1],button)
                            if formType == 'dur': # set new time or maxForms if changed 
                                alt.time = str(round(((float(alt.duration)/1000.0)*((i+1)*0.2))+float(alt.timeRange[0]),3))
                            else:
                                alt.maxForm = str(3+i)
                            plot.xFormButtons += [alt]
                        # make alternate button for current F1 and F2 values (white button)
                        x,y = calculateVowelLocation((plot.currentVowel.F1,plot.currentVowel.F2), plot)
                        buttonRect = pygame.Rect(x,y, 10, 10)
                        buttonRect.center = (x,y)
                        button = pygbutton.PygButton(buttonRect, '◉'.decode('utf8'), border = False) # make new button 
                        button.bgcolor = WHITE 
                        button.fgcolor = plot.currentVowel.button.fgcolor
                        alt = plot.currentVowel.makeAlternate(plot.currentVowel.F1,plot.currentVowel.F2, button)
                        plot.xFormButtons += [alt]
                        chooseFormants = True

                for v in vowList: # deal with all vowels currently displayed on screen
                    if 'enter' in v.button.handleEvent(event):
                        # write the vowel information to the display bit (lower right of the screen)
                        writeInfo(v,plot)
                        plot.currentVowel = v
                        if play: # play the vowel sound (if play mode is on), plays 25 milliseconds on either side of measurement point
                            call(['play',v.wFile,'trim',str(float(v.time)-0.1), '='+str(float(v.time)+0.1)])  
                
            else:  # if chooseFormants == True
                if praatMode: 
                    if not plot.xFormButtons: # make alternate button for current F1 and F2 values (white button)
                        buttonRect = plot.currentVowel.button.rect.inflate(2,2)
                        button = pygbutton.PygButton(buttonRect, '◉'.decode('utf8'), border = False)
                        button.bgcolor = WHITE
                        button.fgcolor = plot.currentVowel.button.fgcolor 
                        alt = plot.currentVowel.makeAlternate(plot.currentVowel.F1, plot.currentVowel.F2 ,button)
                        plot.xFormButtons = [alt]
                    if isfile(praatLog): # this file exists if Log1 has been pressed in the open praat window
                        praatInfo = [(p.split()[0].strip(), p.split()[1].strip() ,p.split()[2].strip(), p.split()[3].strip()) for p in open(praatLog,'rU').readlines()]
                        call(['rm',praatLog])
                    if praatInfo: # if a vowel has been remeasured in praat this will have info in it: (f1,f2,f0)
                        for p in praatInfo: # make a button on the screen for each vowel measured in praat
                            x,y = calculateVowelLocation((float(p[1]),float(p[2])), plot)
                            buttonRect = pygame.Rect(x,y, 8, 8)
                            buttonRect.center = (x,y)
                            button = pygbutton.PygButton(buttonRect, '►'.decode('utf8'), border = False)
                            button.bgcolor = BLACK
                            button.fgcolor = BLACK 
                            alt = plot.currentVowel.makeAlternate(float(p[1]),float(p[2]),button)
                            alt.time = str(round(float(p[0]),3))
                            try: alt.pitch = p[3]
                            except: pass 
                            plot.xFormButtons += [alt]
                        praatInfo = []

                for b in permButtons[1]: # enable you to cancel a remeasurement if necessary with the cancel button
                    if 'click' in b.handleEvent(event):
                        if 'Cancel'in b.caption:
                            plot.xFormButtons = []
                            chooseFormants = False
                            call(['support_scripts/sendpraat', '0', 'praat', 'Quit'])
                            vowelChange = True
                            

                for x in plot.xFormButtons: # choose new formant
                    if 'click' in x.button.handleEvent(event): # click on black or white button to set new vowel location 
                        for vb in plot.vowButtons: 
                            if vb.button is x.origButton:  # change old vowel to remeasured one
                                x.button.fgcolor = vb.button.bgcolor if vb.button.bgcolor != WHITE else vb.button.fgcolor
                                x.button.bgcolor = WHITE
                                if x.button.caption != '►'.decode('utf8'):
                                    x.button.caption = '►'.decode('utf8')
                                    b.rect = b.rect.inflate(-2,-2)
                                plot.vowButtons.remove(vb)
                                plot.vowButtons.append(x)
                                currentVowel = x
                                call(['support_scripts/sendpraat', '0', 'praat', 'Quit'])
                                plot.oldv = vb
                        # write the information of the changed vowel to the list (to write to the log file later)
                        newInfo = [str(wr) for wr in [plot.oldv.id, x.name,x.word,plot.oldv.time,x.time,x.duration,x.stress,x.maxForm,plot.oldv.F1,x.F1,plot.oldv.F2,x.F2]]
                        plot.allLogs[plot.oldv.wFile] += [newInfo]
                        chooseFormants = False
                        plot.xFormButtons = []
                        writeInfo(x,plot)
                        plot.praatInfo = []
                        lastVowel = plot.currentVowel              
                        vowelChange = True
        
        for b in permButtons[1]: # make a list of which stress types are displayed (0,1,2)
            if b.caption in ['1','2','0']:
                if plot.filtered: b.bgcolor = Color("darkolivegreen4")
                if b.bgcolor == Color("darkolivegreen2"):                            
                    plot.stressFiltered += [b.caption]

        if vowelChange: # if the vowel plot needs to be updated
            vowList = []
            if vowelMode == 'intersect': # update displayed as intersect of celex and arpabet vowels
                for v in plot.vowButtons:    
                        if (v.name in plot.arpDisplayed) and (v.celex in plot.celDisplayed):
                            vowList += [v] if v not in plot.filtered else []
            else: # update displayed as union of celex and arpabet vowels
                for v in plot.vowButtons:    
                    if (v.name in plot.arpDisplayed) or (v.celex in plot.celDisplayed):
                        vowList += [v] if  v not in plot.filtered else []
        
        # only let those with the allowed stress be displayed
        vowList = [v for v in vowList if v.stress not in plot.stressFiltered]
        plot.stressFiltered = []

        #### Everything below this is the bit that actually draws to the screen ####

        # draw the vowel plot if it has been updated
        if vowelChange:
            plot.display.fill(WHITE)
            if plot.ellip: # draw confidence ellipse
                plot.display.blit(plot.ellip[0],plot.ellip[1])
            plot.display.blit(F1,(plot.width-myfont.size('F1')[0],plot.height/2)) # draw F1 and F2 as axis labels for the plot
            plot.display.blit(F2,(plot.width/2,10))
            drawGrid(numFont, plot) # draw the grid on the plot
            if zoomLines: pygame.draw.lines(plot.display,BLACK,True,zoomLines,1) # draw the box to zoom to/remove vowels from 
            for b in [v.button for v in vowList]: # draw all vowel tokens to the screen
                b.draw(plot.display) 
            vowelChange = False
        else:  # if it hasn't been updated, update the rest of the screen only
            for r in NOTPLOTRECTS:
                pygame.draw.rect(plot.display,WHITE,r)

        pygame.draw.lines(plot.display,BLACK,True, [(490,plot.height),(plot.width,plot.height),(plot.width,840),(490,840)],2) # draw rectangle to display vowel info
        pygame.draw.lines(plot.display,BLACK,True, [(10,10),(plot.width,10),(plot.width,plot.height),(10,plot.height)],2) # draw rectangle to display vowel buttons
        tokenNum = myfont.render(str(len(vowList)),1,BLACK) # render and draw the number of tokens currently on the screen 
        plot.display.blit(tokenNum,(710,820))
        pygame.draw.lines(plot.display,BLACK,True,[(10,630),(185,630),(185,840),(10,840)],2) # draw the box for the arpabet vowels
        pygame.draw.lines(plot.display,BLACK,True,[(225,630),(480,630),(480,840),(225,840)],2) #draw the box for the celex vowels 
        plot.display.blit(celLabel,(320,605)) # draw CELEX 
        plot.display.blit(arpLabel,(50,605)) # draw ARPABET

        # draw the minimum duration or the removed word if set
        if (plot.minDur or plot.filtWrd) and plot.filtered:
            if plot.minDur:
                filteredCode = ( miniFont.render('Minimum Duration: ',1,BLACK), miniFont.render(str(plot.minDur),1,BLACK) )
                filtsize = miniFont.size(str(plot.minDur))
            else:
                filteredCode = ( miniFont.render('Filtered Word: ',1,BLACK) , miniFont.render(str(plot.filtWrd),1,BLACK) )
                filtsize = miniFont.size(str(plot.filtWrd))
            for i,f in enumerate(filteredCode):    
                plot.display.blit(f,(WINDOWWIDTH-(filtsize[0]+10 if i else 110),WINDOWHEIGHT-50 + i*(filtsize[1]+3)))
        
        for b in permDisplay: # draw all buttons
            b.draw(plot.display)
        
        if plot.textList:    # draw info for last vowel scrolled over to screen
            for i,t in enumerate(plot.textList):
                label = textListFont.render(t, 1, BLACK)
                plot.display.blit(label, (500, 605+(21*i)))
        
        if chooseFormants: # draw alternate formant buttons (when in choose formant mode)
            for xf in plot.xFormButtons:
                xf.button.draw(plot.display)
        
        pygame.display.update() # update screen
        FPSCLOCK.tick(FPS) # screen updates at 10 frames per second (unless FPS set to something else)

if __name__ == '__main__':
    main()