# Natural language intent:
# Execute arbitrary PowerShell commands on a remote computer.

Invoke-Command -ComputerName <RemoteComputerName> -ScriptBlock {<PowerShell commands>}
