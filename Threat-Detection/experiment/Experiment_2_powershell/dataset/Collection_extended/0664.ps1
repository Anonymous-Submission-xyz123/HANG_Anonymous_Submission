# Natural language intent:
# Retrieve and format information about recorded TV items.

Get-IndexedItem -Filter "system.kind = 'recordedTV'" -order 'System.RecordedTV.RecordingTime' -path '\atom-engine\users' -recurse | format-list path,title,episodeName,programDescription
