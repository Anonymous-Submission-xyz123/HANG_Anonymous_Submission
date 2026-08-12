# Natural language intent:
# Delete all Volume Shadow Copies using PowerShell.

Get-WmiObject Win32_Shadowcopy | ForEach-Object {$_.Delete();}
