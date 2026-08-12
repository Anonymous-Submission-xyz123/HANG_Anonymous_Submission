# Natural language intent:
# Retrieve and format information about recorded TV items using PowerShell.

Get-IndexedItem -Filter "system.kind = 'recordedTV'" -order 'System.RecordedTV.RecordingTime' -path '\Cloud-engine\Alice' -recurse | format-list path,title,episodeName,programDescription
