# Natural language intent:
# Removes an item specified by the path and includes the '-Recurse' parameter to remove items in subdirectories.

Remove-Item -Path ${folder} -Recurse
