# Natural language intent:
# Download a file from a remote URL using PowerShell

Invoke-WebRequest "https://raw.githubusercontent.com/redcanaryco/atomic-red-team/master/atomics/T1074.001/src/Discovery.bat" -OutFile ${output_file}
