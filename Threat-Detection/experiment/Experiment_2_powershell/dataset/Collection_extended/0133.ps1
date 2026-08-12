# Natural language intent:
# Retrieve indexed items matching the filter 'stingray' from the My Pictures folder and its subfolders.

Get-IndexedItem -filter stingray -path ([system.environment]::GetFolderPath( [system.environment+specialFolder]::MyPictures )) -recurse
