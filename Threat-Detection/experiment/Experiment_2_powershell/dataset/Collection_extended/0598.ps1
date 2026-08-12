# Natural language intent:
# Invoke a command on a remote system using PowerShell

Invoke-Command -ComputerName <RemoteComputerName> -ScriptBlock {Start-Process cmd.exe -ArgumentList "/c <command>"}
