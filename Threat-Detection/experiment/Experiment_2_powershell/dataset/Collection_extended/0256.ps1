# Natural language intent:
# Import the Powerview module, retrieve NetUser information with SPN, and convert the output to JSON.

Import-Module .\powerview.ps1 -Force; ; Get-NetUser -SPN | ConvertTo-Json -Depth 1
