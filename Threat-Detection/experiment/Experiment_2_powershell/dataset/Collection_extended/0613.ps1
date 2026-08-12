# Natural language intent:
# Retrieve and filter process information using PowerShell

$ps = get-process | select ProcessName,id; ; $valid = foreach($p in $ps) { if($p.ProcessName -eq "lsass") {$p} }; ; $valid | ConvertTo-Json
