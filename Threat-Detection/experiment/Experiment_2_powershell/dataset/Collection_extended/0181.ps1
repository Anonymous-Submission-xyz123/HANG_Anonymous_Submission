# Natural language intent:
# Imports the 'powerview.ps1' module and retrieves information about users with admin count using PowerShell.

Import-Module .\powerview.ps1 -Force; ; Get-NetUser -AdminCount | ConvertTo-Json -Depth 1
