# Natural language intent:
# Copies a file with specific filtering conditions, likely part of a larger operation.

Copy-Item ${host.file.path[filters(technique=T1005,max=3)]} ${host.dir.staged[filters(max=1)]}
