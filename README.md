plotmish
========

Description:

Plotmish is a python based alternative to Plotnik (Labov, http://www.ling.upenn.edu/~wlabov/Plotnik.html).   
Plotmish graphically displays vowels based on the first two formant values for easy identification of outliers. Outliers can then be remeasured automatically based on either time or maximum formant values or remeasured manually in Praat. 
Plotmish also offers several filtering and vowel identification options that are outlined below. 

-----------------------------------------------------------------------------------------

Requirements:

Python (preferably version 2.7) - https://www.python.org/download/releases/2.7
Pygame - http://www.pygame.org/download.shtml
Sound eXchange (SOX) - http://sox.sourceforge.net/

currently only works on OSX

-----------------------------------------------------------------------------------------

Author and Acknowledgements:

Author: Misha Schwartz

Code for plotting confidence ellipses adapted from: Jaime from stackoverflow.com/questions/20126061/creating-a-confidence-ellipses-in-a-sccatterplot-using-matplotlib
	
Code for inputbox.py adapted from: Timothy Downs from http://www.pygame.org/pcr/inputbox/

Code for pygbutton.py (slightly) adapted from: Al Sweigart from https://github.com/asweigart/pygbutton

Code for the name_in_objects_list function in zoomIn.praat adapted from: Ingrid Rosenfelder from PlotnikButton.praat (available with the plotnik 10.3 release at http://www.ling.upenn.edu/~wlabov/Plotnik.html) 

sendpraat binaries from Paul Boersma at http://www.fon.hum.uva.nl/praat/sendpraat.html

The CMU pronunciation dictionary was adapted from the most recent release at http://www.speech.cs.cmu.edu/cgi-bin/cmudict

Also thanks to Morgan Sonderegger, Thea Knowles and the rest of the McGill MLML team. 

-----------------------------------------------------------------------------------------

Running Plotmish:

Plotmish can either be run directly from the command line or using the start up GUI start_plotmish.py . Both are good options but start_plotmish.py is nice because you can save default settings and run the helper scripts updateFormants.py and getPitch.Praat directly from there.  

From the command line:

cd to the plotmish folder and run plotmish as:

python plotmish.py [arguments]

Arguments are:
	positional arguments:
  		vowel info        	formant.txt file or folder containing many
  		wav file          	.wav file or folder containing many
  		annotator         	what's your name?

	optional arguments:
  		-h, --help        	show help message and exit
  		-k 		        	keyword for selecting files in a directory, default is all files in the directory
  		-o 		    	change folder to write log files to, default is plotmish/logs
  		-a                	append to older log file instead of writing over it
  		-p 	         	change path to Praat application, default is /Applications/Praat.app
  		-f0 		 	folder containing pre-generated pitch tracks for each sound file
  		-c                	path to epw.cd celex dictionary file, will then run in celex mode, default is ARPABET mode
	
-----------------------------------------------------------------------------------------

Input files:


vowel info files should be tab delimited text files named something that ends in formant.txt (ex: example_file_formant.txt).  
There should be a row with column headings that correspond to the headings in the config.txt file.  The formant.txt files can have anything written above the headings row.  See the config.txt file for the required and optional columns in the formant.txt file and the example files in the examples/ folder. 
If you want to name a column something other than the default column headings you can do this by changing the heading names in the config.txt file    

