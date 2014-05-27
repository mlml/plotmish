procedure name_in_objects_list .path$ .name$ .type$
## from original plotnik file##
	## converts absolute path name of file to be opened into name of that file in the objects list
	## 1) chop off all path prefixes
	last_slash = rindex(.path$, "/")
	if last_slash == 0
		## we might be on a Windows machine, so check for backslashes as well!
		last_slash = rindex(.path$, "\")    
	endif
	.name1$ = right$(.path$, length(.path$) - last_slash)
	## 2) chop off the file extension
	## NEW APPROACH:  just delete everything after the last ".":
	last_dot = rindex(.name1$, ".")
	#printline 'tab$'Index of last dot is 'last_dot'
	if last_dot <> 0
		name2$ = left$(.name1$, last_dot - 1)
		#printline 'tab$'Name without dot is 'name2$'
	else
		name2$ = .name1$
		#printline 'tab$'No dot in filename!
	endif
	## 3) convert special characters in filename
	## \W = not a word
	## (everything that is not [a-zA-Z0-9_] or "-" (single hyphen/minus) is replaced by underscores)
	#'.name3$' = replace_regex$(.name2$, "#", "_", 0)
	#'.name$' = replace_regex$(.name2$, "[^-|\W]", "_", 0)
	blubb$ = replace_regex$(name2$, "[^-|\W]", "_", 0)
	#printline Blubb is 'blubb$'
	'.name$' = blubb$
endproc

form Get input file names and time of measurement
	sentence Path_of_sound_file
	sentence Current_dir 
	real time_of_measurement
	real play_me
	real maxForms 
endform


Open long sound file... 'Path_of_sound_file$'

call name_in_objects_list "'Path_of_sound_file$'" name_of_sound_file_in_objects_list$ "LongSound"
select LongSound 'name_of_sound_file_in_objects_list$'

View

editor LongSound 'name_of_sound_file_in_objects_list$'

Log settings... "Log file only" 'Current_dir$' "'time''tab$''f1:0''tab$''f2:0''tab$''f0:0'" "Log file only" "NONE" "'time:6''tab$''f0:2'" "NONE" "NONE"  

Formant settings... "5500" 'maxForms' "0.025" "30" 1

zoom_start = time_of_measurement - 0.25
zoom_end = time_of_measurement + 0.25


Zoom... zoom_start zoom_end



## move cursor to point of measurement
Move cursor to... 'time_of_measurement'

if play_me == 1
	## Play window
	Play window
endif
