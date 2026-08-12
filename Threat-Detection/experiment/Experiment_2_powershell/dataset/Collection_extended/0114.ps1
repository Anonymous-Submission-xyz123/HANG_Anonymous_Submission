# Natural language intent:
# Retrieve indexed items from the specified path, filter by camera maker, and group by focal length.

Get-IndexedItem -path c:\ -recurse  -Filter cameramaker=pentax! -Property focallength | group focallength -no | sort -property @{e={[double]$_.name}}
