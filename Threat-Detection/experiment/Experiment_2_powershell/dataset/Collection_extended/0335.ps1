# Natural language intent:
# Start a process based on the results of a filtered and sorted indexed item search.

start (Get-IndexedItem -filter stingray -path OneIndex14:// -recurse -first 1 -orderby rank)
