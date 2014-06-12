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
        self.altVow = ''
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
        self.remeasureOpts = ['praat'] 

    def makeAlternate(self, f1, f2, newButton):
        # makes identical version of vowel with different f1 and 
        # f2 and button
        newV = vowel(f1,f2, self.wFile)
        newV.name = self.name
        newV.stress = self.stress
        newV.duration = self.duration
        newV.word = self.word
        newV.time = self.time
        newV.altVow = self.altVow
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
        newV.remeasureOpts = self.remeasureOpts 
        return newV

    def inPlot(self, plot):
        # returns bool whether button is in the current plot
        under = self.button.rect.center[1] > 10 
        over = self.button.rect.center[1] < plot.height
        right_of = self.button.rect.center[0] > 10
        left_of = self.button.rect.center[0] < plot.width
        
        return under and over and right_of and left_of  

# placeholder class for vowel plot
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
        self.altDisplayed = [] # list of celex vowels to display on plot
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

# placeholder class for plotmish settings
class Settings:
    def __init__(self):
        self.start, self.stop = (),() # tuples of the corners of the section of the plot to zoom in on (or remove buttons from)
        self.zoomLines = None # lines to draw when zooming or removing a group of buttons
        self.vowelChange = True # set to True to change the vowel plot (necessary for continuous running with large numbers of vowels)
        self.play = False # indicates whether play button in on or off
        self.zooming = False # whether zoom button is on or off (and zoom mode is on)
        self.stdDevCounter = 0 #counter for drawing different ellipse sizes
        self.formType = 'dur' # remeasure mode (either 'dur' or 'num')
        self.praatMode = True # true if remeasure mode is praat (button caption is remeasureP)
        self.vowelMode = 'union' # vowel display mode: union or intersect of vowels in arpDisplayed and altDisplayed
        self.chooseFormants = False  # True if you are re-evaluating formant measurements 
        self.praatInfo = [] # list to write info from praatlog
        self.lastVowel = None # last vowel measured (for used with "check last" button)
        self.vowList = [] # list to write vowel that are currently displayed
        self.displayMemory = [] # list of all vowel plots up to the last save
        self.logMemory = [] # list of all log dicts up to the last save
        self.praatLog = None # set path of praatlog file (location of output of praat)     
        self.permButtons = [] # make permanent buttons (vowel buttons, display all/none buttons)
        self.permDisplay = [] #put all permanent buttons in a list so they can be displayed
        self.files = []
        self.FPS = 10 
        self.F1,self.F2 = None, None
        self.arpLabel = None
        self.celLabel = None 
