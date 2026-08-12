# Natural language intent:
# Invoke a command on a remote system using PowerShell

Invoke-Command -ComputerName <target computer> -ScriptBlock {Invoke-Expression -Command <malicious code >}
