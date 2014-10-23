plotmish
========

***NEW READ ME***

## **Description**
Plotmish is a python-based formant remeasurement tool. It can be used to correct errors made by automatic formant measurements programs and to annotate the changes.

Plotmish graphically displays vowels based on the first two formant values for easy identification of outliers. Outliers can then be remeasured automatically based on either time or maximum formant values or remeasured manually in Praat.

Plotmish also offers several filtering and vowel identification options that are outlined below.

> Plotmish is inspired by [Plotnik](http://www.ling.upenn.edu/~wlabov/Plotnik.html) (Labov)

***
## **Requirements**
[Python](https://www.python.org/download/releases/2.7) (preferably version 2.7)

[Pygame](http://www.pygame.org/download.shtml)

[Sound eXchange (SOX)](http://sox.sourceforge.net/)

[Praat](http://www.praat.org/)

Currently only works on OSX.

***
## **Author and Acknowledgements**
**Author** Misha Schwartz

**Acknolwedgements**
Code for plotting confidence ellipses adapted from: Jaime, [stackoverflow.com/questions/20126061/ creating-a-confidence-ellipses-in-a-sccatterplot-using-matplotlib](stackoverflow.com/questions/20126061/ creating-a-confidence-ellipses-in-a-sccatterplot-using-matplotlib)

Code for inputbox.py adapted from: Timothy Downs, [http://www.pygame.org/pcr/inputbox/](http://www.pygame.org/pcr/inputbox/)

Code for the `name_in_objects_list` function in `zoomIn.praat` adapted from: Ingrid Rosenfelder, `PlotnikButton.praat` (available with the plotnik 10.3 release at [http://www.ling.upenn.edu/~wlabov/ Plotnik.html](http://www.ling.upenn.edu/~wlabov/ Plotnik.html))

sendpraat binaries: Paul Boersma, [http://www.fon.hum.uva.nl/praat/sendpraat.html](http://www.fon.hum.uva.nl/praat/sendpraat.html)

The [CMU pronunciation dictionary](http:// www.speech.cs.cmu.edu/cgi-bin/cmudict), adapted from the most recent release

Also thanks to Morgan Sonderegger, Thea Knowles and the rest of the McGill MLML team.

***
# **Running Plotmish**
Plotmish can either be run directly from the command line or using the start up GUI `start_plotmish.py`. Both are good options but `start_plotmish.py` is nice because you can save default settings and run the helper scripts `updateFormants.py` and `getPitch.Praat` directly from there.

## **From the command line**
cd to the plotmish folder and run plotmish as:

python plotmish.py [arguments]
### **Command Line Arguments**

	positional arguments:
  		vowel info        	formant.txt file or folder
  		wav file          	.wav file or folder
  		annotator         	what's your name?

	optional arguments:
  		-h, --help        	show help message and exit
  		-k 		        	keyword for selecting files in a directory, default is all files in the directory
  		-o 		    	change folder to write log files to, default is plotmish/logs
  		-a                	append to older log file instead of writing over it
  		-p 	         	change path to Praat application, default is /Applications/Praat.app
  		-f0 		 	folder containing pre-generated pitch tracks for each sound file
  		-c                	path to epw.cd celex dictionary file, will then run in celex mode, default is 
					ARPABET mode

### **Command Line Input Files**
Vowel info files should be tab delimited text files named something that ends in _**-formant.txt**_ `(ex: example_ _file-formant.txt)`.

There should be a row with column headings that correspond to the headings in the _**config.txt file**_. The formant.txt files can have anything written above the headings row.

See the config.txt file for the required and optional columns in the formant.txt file and the example files in the examples/ folder.

#### **To edit default column headings**

> If you want to name a column something other than the default column headings you can do this by changing the heading names in the config.txt file. For example, if you want the column containing the arpabet pronunciation of the vowel to be called 'arpVow' you should change the first line in the config.txt file from:


> ARPABET : vowel # arpabet vowel token (with or without stress)

> to

> ARPABET : arpVow # arpabet vowel token (with or without stress)

For further details on the required and optional columns in the formant.txt files see the comments (everything to the right of the #) in the config.txt files

The default config.txt file is configured to use the output of FAVE-extract (faav.something.com). If using the output of FAVE-extract, add the line:

`candidates=T`

to the config file in the FAVE-extract main directory in order to get all of the alternate measurements.

#### **Naming Input Files**
The wav files should be .wav configured sound files that correspond to the formant.txt files. They should be named the same as
the -formant.txt files.

For example, two corresponding files should be named:

`example_file-formant.txt` and `example_file.wav`

#### **Pitch Tracks**
Pitch tracks are pitch files generated using Praat that correspond to the wav files.

The pitch track for `example_file.wav` should be called `example_file.Pitch`. Pitch tracks for your wav files can be automatically generated by running `getPitch.Praat` or by clicking the 'Make Pitch Tracks' button in `start_plotmish.py`.

The location of these files should be specified with the -f0 flag on start up or by writing it in the 'Pitch Tracks' line in `start_plotmish.py`.

Pitch tracks are optional and are not required to run plotmish.

### **Other Plotmish Command Line Arguments**

	annotator 	:	who is annotating the file (made mandatory to encourage good practice)
	-k		: 	specify a keyword to filter the files to use.  For example: using the keyword 'day10' will only
				run files with that string in the basename.
	-o		:	all changes are written to log files saved in the folder specified here (default is log/)
	-a		: 	append to the currently saved log files instead of writing over them
	-p		:	specify the location of Praat (default is /Applications/Praat.app
	-c		: 	specify the epw.cd celex dictionary if you want to run in Celex mode (see below) 

## **Modes**
Plotmish can run in two modes: ARPABET or CELEX

### **ARPABET**
In ARPABET mode you are given the option to display vowels based on their actual pronunciation as well as their unreduced pronunciation. For example, if the vowel in the word 'TO' is pronounced as 'T AH0' you can also display it with it's unreduced pronunciation: 'T UW1' .

### **CELEX**
In celex mode, instead of the unreduced pronunciation in the arpabet phones you are given the option to display the vowels based on their pronunciation using the celex phones. Mapping to CELEX phones is not a one-to-one measurement, but instead calculated using the word’s pronunciation in the celex dictionary and MapToCelex.py .

# **Using Plotmish**
## **Displaying Vowels**
When you first start plotmish there will be no vowels displayed on the screen. To display all the vowels click the 'Show All' button. To display only certain vowels, click on the corresponding vowel button on the bottom left of the screen.
_For example:_ clicking 'AH' will display all the 'AH' vowels to the screen.

Depending on the mode, the vowel buttons in the middle of the screen near the bottom will also display different vowels (see Modes above). Clicking a vowel button again will remove the vowel from the screen and clicking the 'Clear' button will remove all buttons from the screen.

The union / intersect button is between the two sets of vowel buttons. Clicking this toggles whether the vowels displayed are those that are selected in both the sets of vowels (intersect) or in at least one of the sets (union).

## **The Vowel Plot**

Vowels are displayed on the vowel plot according to their F1 (vertical axis) and F2 (horizontal axis) values.

The numbers in the corners of the plot show the maximum and minimum values (in Hz) displayed on the plot. The grid lines are every 50 Hz for F1 and every 100 Hz for F2.

The total number of vowels displayed on the plot is shown in the bottom right corner of the screen.

## **Reading Vowel Information**
When a vowel is displayed to the plot you can scroll over it to get the information about the vowel. This information includes the vowel name, F1 and F2 values, stress, duration, etc. and is displayed to the box in the bottom right corner of the screen.

You can also hear the vowel by scrolling over it when the 'Play' button is dark green (click to toggle the 'Play' button) Finally, you can view the vowel in Praat by holding spacebar and clicking the vowel. Note that by doing this you will not be able to remeasure the vowel like in RemeasureP mode (see below)

## **Remeasuring a Vowel**
Vowels can be remeasured in 3 different ways: in praat, by duration and by maximum formant values.

> The 'Remeasure' button shows which type is to be used: **RemeasureP, Remeasure%, RemeasureF**

You can change which type by clicking this button. When a the Praat option is selected, clicking a vowel will open up that vowel in Praat. You can then change the settings in Praat and move the cursor as you see fit.

### **To make a RemeasureP measurement**
click: `Query > Log 1 (F12)` and plotmish will draw a black vowel on the screen with those measurements. You can make multiple remeasurements in Praat.

Then go back to plotmish and click on the remeasured vowel you would like to change to. You can always select the original vowel (in white with a coloured border) as well.

### **To make a Remeasure% measurement**
clicking on a vowel will show 5 new vowels (in black) measured at 20%, 35%, 50%, 65%, 80% of the vowel's duration. Click on the remeasured vowel you would like to select.

### **To make a RemeasureF measurement**
clicking on a vowel will show the vowel measured at the same time but with a maximum formant setting of 3, 4, 5, and 6 respectively. Once again, click on the desired vowel to change it. At any time with any remeasurement option, you can clickcancel to stop remeasuring.

## **Filtering Vowels**
Plotmish provides the option to filter vowels based on minimum duration and word orthography.

### **To filter vowels based on minimum duration**
click the `Dur. Filter` button and then type in the minimum duration in milliseconds you want to display to the screen. This will remove all vowels that are currently displayed to the screen that have a duration of less than the specified amount.

Note that this will not remove the vowels, to remove them completely, click the button again which should now be called `Rmv.Dur.Filt` and they will be removed permanently. If you choose not to remove the vowels they can be redisplayed by clicking any vowel button or `Show All`.

### **To filter based on word orthography**
use the same process as filtering based on minimum duration except click the button `Wrd.Filter` and then type the word you want to filter (not case sensitive).

If a vowel occurs in the specified word then the vowel is filtered.

_Note that you can't filter by duration and word orthography at the same time._

You can also filter by stress (though you can't remove these filtered vowels). The three buttons called '1','2','0', all correspond to different stress types. If they are dark green, vowels with that stress type will be shown, if they are light green they will not be shown.

Clicking on these buttons toggles them.

_Note: '1' = primary stress , '2' = secondary stress, '0' = no stress_

## **Removing a Vowel**
It is often quite useful to remove a vowel entirely from the screen. This can be done for several reasons. If no remeasurements for a given vowel is acceptable it can be removed as a 'Bad' vowel. Also, if a vowel does not require remeasurement or has been remeasured and now is ok, it can also be removed so as to reduce clutter on the vowel plot.

### **To remove a vowel**
First, make sure you set the correct reason for removal by clicking the button `'Rmv. OK'`/`'Rmv. Bad'` button. (As you might expect you want it to say OK if you removing good vowels and Bad if you're removing bad vowels).

Then, click on a vowel while holding down the control button.

#### **To remove a vowel and leave a note**
This allows you to enter a reason why the vowel is being removed.
Hold down `control+shift`and a text entry box will appear.

#### **To remove a group of vowels at once**
Hold down the `A` key and click and drag over the region you want to remove.
Release your mouse click _before_ releasing `control+A` to clear the region.
`control+shift+A` allows an annotator to leave a note for an entire region.

## **Zooming**
To zoom into the plot, click the `Zoom` button so it becomes dark green and then click and drag over the region you want to zoom in to. Click `Reset Zoom` to go back to the whole plot.

## **Other Buttons**
**Std Dev:** display ellipses showing 1, 2, and 3 standard deviations from the mean of the vowels currently displayed on screen

**Save:** Save all changes up to this point to the log files

**Undo:** Undo most recent change (can be repeated back to the most recent save)

**Check Last:** Open most recently changed vowel in Praat (cannot remeasure)

**Resume:** Read all previously made (must be previously saved!) changes from the log files and update the plot accordingly

## **Other Files**
### `getPitch.Praat`
generates pitch tracks for wav files (see section on **Running Plotmish: Pitch Tracks** above)
### `updateFormants.py`
writes new formant.txt files with changes in log files taken into account.

Can either be run by clicking the `Update Formants` button in `start_plotmish.py` or on the command line with the following arguments:

	formant_files         	directory containing formant.txt files or a single formant.txt file to be corrected
	
	optional arguments:
	-h, --help           	show this help message and exit
	-l, -logs       	plotmish logs change folder containing plotmish correction logs.
                                Can also be a single csv file.
                                Default is log.     
	-c,  -corrected     	change folder to write corrected formant.txt files to, default is corrected/ 
	
	
# **Examples**
Plotmish comes with an example formant.txt file so you can test out plotmish before running it on your own files if you wish. The example is called s0101a-formant.txt and it can be found in the examples/ folder.

To run plotmish with this file you must first get the corresponding wav file. This can be found by downloading the free buckeye natural speech corpus [http://buckeyecorpus.osu.edu/] (http://buckeyecorpus.osu.edu/).

The wav file you want should be the first one in the corpus called: s0101a.wav

This file can be run with the default config file.

# **Have fun.**



