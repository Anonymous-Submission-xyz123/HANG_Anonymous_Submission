# Natural language intent:
# Copy the specified input file to the specified output file, start a process with the output file, get the process ID, and stop the process.

copy ${inputfile} ${outputfile} ; $myT1036_003 = (Start-Process -PassThru -FilePath ${outputfile}).Id ; Stop-Process -ID $myT1036_003
