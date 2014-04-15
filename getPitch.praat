
procedure name_in_objects_list .path$ .name$ .type$

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

form Get input file names and time of measurement	sentence keyword *
endform

directory_path$ = chooseDirectory$: "Choose a directory containing the wav files"
directoryName$ = chooseDirectory$: "Choose a directory to save all the pitch files"


strings = Create Strings as file list: "list", directory_path$ + "/*.wav"

numberOfFiles = Get number of strings
for ifile to numberOfFiles
	selectObject (strings)
    	fileName$ = Get string: ifile
	if index_regex(fileName$, keyword$) != 0
    		Read from file: directory_path$ + "/" + fileName$
    		call name_in_objects_list "'fileName$'" name_of_sound_file_in_objects_list$ "LongSound"
    		select Sound 'name_of_sound_file_in_objects_list$'
    		To Pitch... 0.0 75 600 
		select Pitch 'name_of_sound_file_in_objects_list$'
		Save as text file:  directoryName$ + "/"+ name_of_sound_file_in_objects_list$ + ".Pitch"
		Remove
		select Sound 'name_of_sound_file_in_objects_list$'
		Remove
	endif
endfor

selectObject (strings)
Remove

