# Natural language intent:
# Invoke a web request to download a file from a specified URL and save it to a local file.

Invoke-WebRequest "https://raw.githubusercontent.com/redcanaryco/atomic-red-team/master/atomics/T1074.001/src/Discovery.bat" -OutFile ${OutputFILE}
