# Natural language intent:
# Execute a malicious command on a remote system using PowerShell.

Invoke-Command -ComputerName [Remote System] -ScriptBlock {[Malicious Command]}
