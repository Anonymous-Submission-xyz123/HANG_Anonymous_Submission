# Natural language intent:
# Invokes a command on a remote system using PowerShell remoting.

Invoke-Command -ComputerName <target_system> -ScriptBlock { <command> }
