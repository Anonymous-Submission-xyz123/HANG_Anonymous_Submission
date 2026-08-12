# Natural language intent:
# Collects information about processes, specifically targeting "lsass" process.

$ps = get-process | select processname,Id; ; $valid = foreach($p in $ps) { if($p.ProcessName -eq "lsass") {$p} }; ; $valid | ConvertTo-Json
