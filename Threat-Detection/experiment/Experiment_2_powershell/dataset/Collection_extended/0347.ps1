# Natural language intent:
# Use WMIC to get process information and append it to a log file.

wmic process get executablepath,name,processid,parentprocessid >> $env:APPDATA\vmtools.log; ; cat $env:APPDATA\vmtools.log
