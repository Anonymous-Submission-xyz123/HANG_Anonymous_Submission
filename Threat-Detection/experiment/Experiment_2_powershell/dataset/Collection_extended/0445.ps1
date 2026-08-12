# Natural language intent:
# Invoke a script block that retrieves process information and writes it to a file using PowerShell.

Invoke-Expression -Command {& {Get-Process | Out-File c:\temp\process.txt}}
