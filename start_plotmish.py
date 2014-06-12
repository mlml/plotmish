import sys, os, subprocess, glob
from pygame.locals import *

sys.path.append('plotmish/support_scripts')

import pygame, pygbutton, inputbox

WINDOWWIDTH, WINDOWHEIGHT = 500, 750

captionFont = pygame.font.SysFont('courier',16)

sendpraat = os.path.join(os.getcwd(),'plotmish','support_scripts','sendpraat')

getPitch = os.path.join(os.getcwd(),'plotmish','getPitch.praat')

updateFormants = os.path.join(os.getcwd(),'plotmish','updateFormants.py') 

plotmish = os.path.join(os.getcwd(), 'plotmish', 'plotmish.py')

FPS = 10

WHITE = (255, 255, 255)
BLACK = (0,0,0)
GREY = Color('gray20')

pygame.init()
DISPLAYSURFACE = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
FPSCLOCK = pygame.time.Clock()
pygame.display.set_caption('Plotmish')

button = pygbutton.PygButton

args =	{	'formant' : '',
			'wav' : '',
			'keyword' : '',	
			'log' : '',
			'praat' : '',
			'pitch tracks' : '',
			'overwrite' : False,
			'corrected': '', 
			'annotator': '',
			'celex dict': '',
			'mode': False}

defaultsPath = os.path.join(os.getcwd(),'plotmish','defaults.txt')

akeys = {0:'formant',1:'wav',2:'keyword', 3:'log',4:'praat',5:'pitch tracks',6:'celex dict', 7:'corrected', 8: 'annotator'}


def writeDefaults():
	defaultF = open(defaultsPath, 'wb')
	for k,v in args.items():
		defaultF.write(k+'\t'+str(v)+'\n')
	defaultF.close()	

def readDefaults():
	defaultF = open(defaultsPath, 'rb')
	for d in defaultF.readlines():
		if d.strip():
			d = d.replace('\n','').split('\t')
			args[d[0].strip()] = d[1].strip() if d[0] not in ['overwrite', 'mode'] else eval(d[1].strip()) 
	defaultF.close()

def updateArgs():
	for i,b in enumerate(textbuttons):
		args[akeys[i]] = b.caption


def checkDefaults():
	bad = []
	for k,v in args.items():
		if k in  ['formant','wav']:
			if not (os.path.isdir(v) or os.path.isfile(v)):
				if not v:
					bad.append('no entry for '+k)
				else:	
					bad.append(k+' path does not exist')
		if k == 'praat':
			if not v:
				bad.append('no entry for '+k) 
			elif not (os.path.isdir(v) and os.path.basename(v) == 'Praat.app'):
				bad.append('Praat not found at given path')
		if k == 'log':
			if not v:
				bad.append('no entry for '+k)
			elif not os.path.isdir(v):
				if os.path.isdir(os.path.dirname(v)):
					subprocess.call(['mkdir',v])
				else:
					bad.append(k+' path does not exist')
		if k == 'pitch tracks':
			if not os.path.isdir(v) and v:
				bad.append(k+' path does not exist')
			elif not glob.glob(os.path.join(os.path.basename(v),'*.Pitch')) and v:
				bad.append('no Pitch files found in '+k+' folder')
		if k == 'corrected':
			if not os.path.isdir(v) and v:
				bad.append(k+' path does not exist')
			elif not v:
				bad.append('no entry for '+k)
		if k == 'annotator':
			if not v:
				bad.append('no entry for '+k)
		if k == 'celex dict':
			if not os.path.isfile(v) and v:
				bad.append(k+' file not found')
			elif not v and args['mode']:
				bad.append(k +' required for Celex Mode')
	return bad
	
root = os.path.abspath(os.sep)

def shortcut(pth):
	if not pth: 
		return pth
	if pth[0] == '~':
		pth = os.path.expanduser("~")+pth[1:]
	if pth[:2+len(os.sep)] == '..'+os.sep:
		pth = os.path.join(os.path.dirname(pth.split('..'+os.sep,1)[1]),pth.split('..'+os.sep,1)[1])
	elif pth == '..':
		pth = os.path.dirname(os.getcwd())
	if pth[:1+len(os.sep)] == '.'+os.sep:
		pth = os.path.join(os.getcwd(),pth.split('.'+os.sep,1)[1])
	elif pth == '.':
		pth = os.getcwd()	
	try:
		if pth[:len(root)] != root:
			pth = root+pth
	except:
		pth = root+pth
	return pth

def completePath(path):
	immedDir = shortcut(path.rsplit(os.sep,1)[0])
	if os.path.isdir(immedDir):
		suffix = path.rsplit(os.sep,1)[1]
		opts = [os.path.basename(g) for g in glob.glob(os.path.join(immedDir,suffix+'*'))]
		if len(opts) == 1:
			completed = os.path.join(path.rsplit(os.sep,1)[0], opts[0])
			completed += os.sep if os.path.isdir(os.path.join(immedDir,opts[0])) else ''
			return [completed]
	return [path]


def errorMessage(message):
    for i,m in enumerate(message):
        mess = captionFont.render(m,1,BLACK)
        DISPLAYSURFACE.blit(mess,(WINDOWWIDTH/2.0-(captionFont.size(m)[0]/2.0),WINDOWHEIGHT/2.0-(captionFont.size(m)[1]/2.0)+(i*(captionFont.size(m)[1])+5)))
    #pygame.display.update()
    #DISPLAYSURFACE.fill(WHITE)

def resizeText(button):
	fontsize = 16
	while button.rect.width < button._font.size(button.caption)[0] and fontsize > 7:
		fontsize -= 1
		button._font = pygame.font.SysFont('courier',fontsize)
		button._update()

if not os.path.isfile(defaultsPath):
	writeDefaults()
else:
	readDefaults()





textbuttons = [	button(rect = pygame.Rect(20, 100, 460, 20),caption = args['formant'], border = False, bgcolor = GREY, fgcolor = WHITE),
				button(rect = pygame.Rect(20, 150, 460, 20),caption = args['wav'], border = False, bgcolor = GREY, fgcolor = WHITE),
 				button(rect = pygame.Rect(20, 200, 460, 20),caption = args['keyword'], border = False, bgcolor = GREY, fgcolor = WHITE),
 				button(rect = pygame.Rect(20, 250, 460, 20),caption = args['log'], border = False, bgcolor = GREY, fgcolor = WHITE),
 				button(rect = pygame.Rect(20, 300, 460, 20),caption = args['praat'], border = False, bgcolor = GREY, fgcolor = WHITE),
 				button(rect = pygame.Rect(20, 350, 460, 20),caption = args['pitch tracks'], border = False, bgcolor = GREY, fgcolor = WHITE),
 				button(rect = pygame.Rect(20, 400, 460, 20),caption = args['celex dict'], border = False, bgcolor = GREY, fgcolor = WHITE),
 				button(rect = pygame.Rect(20, 450, 460, 20),caption = args['corrected'], border = False, bgcolor = GREY, fgcolor = WHITE), 
 				button(rect = pygame.Rect(20, 500, 460, 20),caption = args['annotator'], border = False, bgcolor = GREY, fgcolor = WHITE)]

for t in textbuttons:
	resizeText(t)

onoffbuttons = [ button(rect = pygame.Rect(20, 550, 200, 20), caption = 'Overwrite Log Files' if args['overwrite'] else 'Append to Log files', bgcolor = pygame.Color('gray46')),
				 button(rect = pygame.Rect(270, 550, 200, 20), caption = 'Celex Mode' if args['mode'] else 'ARPABET Mode', bgcolor = pygame.Color('gray46')),
				 button(rect = pygame.Rect(20, 600, 200, 20), caption = 'Make Pitch Tracks'),
				 button(rect = pygame.Rect(270, 600, 200, 20), caption = 'Set As Default'),
				 button(rect = pygame.Rect(0, 650, 200, 20), caption = 'Update Formants'),
				 button(rect = pygame.Rect(0, 700, 200, 40), caption = 'Start Plotmish')]

for o in onoffbuttons[-2:]:
	o.rect.centerx = WINDOWWIDTH/2.0

errorButton = button(rect = pygame.Rect(270, 550, 200, 20), caption = 'BACK')
errorButton.rect.centerx = WINDOWWIDTH/2.0

buttons = textbuttons + onoffbuttons

text = 	[ 	(captionFont.render('formant.txt files:',1,BLACK),(20,82)),
			(captionFont.render('.wav files:',1,BLACK),(20,132)),
			(captionFont.render('keyword:',1,BLACK),(20,182)),
			(captionFont.render('log folder:',1,BLACK),(20,232)),
			(captionFont.render('praat:',1,BLACK),(20,282)),
			(captionFont.render('pitch tracks:',1,BLACK),(20,332)),
			(captionFont.render('celex pronunciation dictionary:',1,BLACK),(20,382)),
			(captionFont.render('corrected folder:',1,BLACK),(20,432)),
			(captionFont.render('annotator:',1,BLACK),(20,482))]

mode = 'main'

while True: # main loop
	for event in pygame.event.get():
		if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
			pygame.quit() 
			sys.exit()
		
		if mode == 'main':
			for i,b in enumerate(textbuttons):
				if 'click' in b.handleEvent(event):
					answer = []
					while isinstance(answer, list):
						answer = inputbox.ask(DISPLAYSURFACE,'',size = b.rect, newFont = captionFont, currentText = b.caption if not answer else answer[0], pathMode = True if i not in [2,8] else False)
						if isinstance(answer, list):
							answer = completePath(answer[0].strip())
					if answer == 'QUITNOW':
						pygame.quit() 
						sys.exit()

					b.caption = shortcut(answer.strip()) if i not in [2,8] else answer
					resizeText(b)
					updateArgs() 

		
			for b in onoffbuttons:
				if 'click' in b.handleEvent(event):
					if b.caption == 'Overwrite Log Files':
						b.caption = 'Append to Log files'
						args['overwrite'] = False
					elif b.caption == 'Append to Log files':
						b.caption = 'Overwrite Log Files'
						args['overwrite'] = True
					if b.caption == 'ARPABET Mode':
						b.caption = 'Celex Mode'
						args['mode'] = True
					elif b.caption == 'Celex Mode':
						b.caption = 'ARPABET Mode'
						args['mode'] = False
					if b.caption == 'Set As Default':
						errors = checkDefaults()
						if not errors:
							writeDefaults()
						else: 
							mode = 'error'
					if b.caption == 'Make Pitch Tracks':
						errors = [e for e in checkDefaults() if 'praat' in e]
						if not errors:
							subprocess.call(['open', args['praat']])
							subprocess.call([sendpraat, '0', 'praat', 'execute "'+getPitch+'"'])
						else:
							mode = 'error'
					if b.caption == 'Update Formants':
						errors = [e for e in checkDefaults() if 'praat' in 'formant' in e or 'log' in e or 'corrected' in e]
						if not errors:
							subprocess.call(['python', updateFormants, args['formant'], '-l', args['log'], '-c', args['corrected']])
						else:
							mode = 'error'
					if b.caption == 'Start Plotmish':
						errors = [e for e in checkDefaults() if 'corrected' not in e]
						if not errors:
							message = ['python', plotmish, args['formant'], args['wav'],args['annotator'], '-k', args['keyword'], '-o', args['log'], '-p', args['praat'], '-f0', args['pitch tracks'], '-epw', args['celex dict']] 
							if not args['overwrite']:
								message += ['-a']
							if args['mode']:
								message += ['-c']
							subprocess.call(['cd', 'plotmish'])
							subprocess.call(message)
							pygame.event.clear()
						else:
							mode = 'error'

		elif mode == 'error':
			if 'click' in errorButton.handleEvent(event):
				mode = 'main'

	DISPLAYSURFACE.fill(WHITE)
	if mode == 'main':
		for b in buttons: b.draw(DISPLAYSURFACE)
		for t in text: DISPLAYSURFACE.blit(t[0],t[1])
	if mode == 'error':
		errorMessage(errors)
		errorButton.draw(DISPLAYSURFACE)

	pygame.display.update() # update screen
	FPSCLOCK.tick(FPS)

















