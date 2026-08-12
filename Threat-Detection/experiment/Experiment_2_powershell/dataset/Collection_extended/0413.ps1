# Natural language intent:
# Copy files with specified filtering criteria using PowerShell.

Copy-Item ${host.file.path[filters(technique=T1005,max=5)]} ${host.dir.staged[filters(max=2)]}
