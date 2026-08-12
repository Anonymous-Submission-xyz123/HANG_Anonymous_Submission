# Natural language intent:
# Retrieve indexed items matching specific criteria within the specified path, including filtering by kind and title.

Get-IndexedItem -Value 'title' -filter 'kind=recordedtv' -path \atom-engine\SuperUser  -recurse
