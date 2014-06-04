import argparse, os, glob, subprocess, sys

pj,bn = os.path.join, os.path.basename

parser = argparse.ArgumentParser(description = 'Correct formant.txt files based on plotmish logs')
parser.add_argument('formant_files', help = 'directory containing formant.txt files or a single formant.txt file to be corrected')
parser.add_argument('-l','-logs', metavar = 'plotmish logs',default = 'log' , help = 'change folder containing plotmish correction logs. Can also be a single csv file. Default is log/')
parser.add_argument('-c','-corrected', metavar = 'corrected csvs', default = 'corrected', help = 'change folder to write corrected formant.txt files to, default is corrected/')
args = parser.parse_args()

if os.path.isdir('plotmish'):
    os.chdir('plotmish')

## get log files
if os.path.isdir(args.l):
	logs = glob.glob(pj(args.l, '*'))
else:
	logs = [args.l]

## get formant.txt files to be corrected
if os.path.isdir(args.formant_files):
	oldF = glob.glob(pj(args.formant_files,'*'))
else:
	oldF = [args.formant_files]

## make directory to write out files if it doesn't exist
if not os.path.isdir(args.c):
	subprocess.call(['mkdir', args.c])

## read config file
configF = open('config.txt','rU')
configList = [c.split('#')[0].strip().split(':') if '#' in c else c.strip() for c in configF.readlines() if c.split('#')[0]]
configF.close()


## define dictionaries of headings that will be changed in the corrected formant.txt file
headings = ['F1', 'F2', 'TIME', 'MAX FORMANTS']
configDict = {c[0].strip(): c[1].strip() for c in configList if c[0].strip() in headings}
revConfigDict = {v:k for k,v in configDict.items()}

## iterate over all log files
for l in logs:
	
	name = bn(l).rsplit('-',1)
	
	## check that file is named correctly
	if name[1] != 'corrLog.csv':
		print >> sys.stderr, 'Log file %r does not end in -corrLog.csv.  File may have been renamed \nskipping...' %bn(l)
		continue

	oldForms = []
	for o in oldF:
		formName = bn(o).rsplit('-',1)
		try: 
			oldForms += [o] if formName[0] == name[0] and formName[1] == 'formant.txt' else []
		except: pass

	##check that file corresponds to a formant.txt file
	if not oldForms:
		print >> sys.stderr, 'Log file %r does not correspond to a formant.txt file in %r \nskipping...' %(bn(l),bn(args.formant_files))
		continue

	## extract old formant files info to a list
	oldFile = open(oldForms[0],'rU')
	formList = [o.replace('\n','').split('\t') for o in oldFile.readlines()]
	oldFile.close()

	## find indexes to write the changes to
	indexes = {i: None for i in headings}
	badFile = True
	for i,line in enumerate(formList):
		headCount = 0
		for head in configDict:
			if configDict[head] in line: headCount += 1
		if headCount == len(headings):
			for j,li in enumerate(line):
				try: indexes[revConfigDict[li]] = j  
				except: pass
			badFile = False
			topping = formList[:i]
			formList = formList[i:]
			indexes.update({'NOTE':len(line)})
			break
	if badFile:
		print >> sys.stderr, 'Mandatory Headings not found','for file: '+ basename(oldForms[0])+'\nCannot write to file, continuing...'
		continue
	## extract logFile info to a list
	logFile = open(l,'rU')
	logList = [o.replace('\n','').split(',') for o in logFile.readlines()]
	logFile.close()
	## correct formant files
	for ll in logList[1:]:
		number = int(ll[1])
		time = ll[5]
		maxForms = ll[8]
		F1 = ll[10]
		F2 = ll[12]
		try:
			comment = ll[13]
		except:
			comment = 'corrected'
		## change the values where appropriate
		formList[number][indexes['F1']] = F1 if F1 != 'NA' else formList[number][indexes['F1']]
		formList[number][indexes['F2']] = F2 if F2 != 'NA' else formList[number][indexes['F2']]
		formList[number][indexes['TIME']] = time if time != 'NA' else formList[number][indexes['TIME']]
		formList[number][indexes['MAX FORMANTS']] = maxForms if maxForms != 'NA' else formList[number][indexes['MAX FORMANTS']]
		
		## add appropriate note
		reason = comment.split()[0].replace(':','').strip()
		try: 
			note = ' '.join([c.strip() for c in comment.split()[1:]])
		except: 
			note = ''
		try:
			formList[number][indexes['NOTE']] = reason
			formList[number][indexes['NOTE']+1] = note
		except:
			formList[number] += [reason,note]

	## write to new formant.txt file
	newFile = open(pj(args.c,name[0]+'-formant.txt'),'wb')
	for t in topping:
		newFile.write(' '.join(t)+'\n')
	for fl in formList:
		newFile.write('\t'.join(fl)+'\n')
	newFile.close()
