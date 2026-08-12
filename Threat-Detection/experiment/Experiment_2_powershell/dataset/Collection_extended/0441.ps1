# Natural language intent:
# Invoke a command on a remote computer with a specified malicious command using PowerShell.

Invoke-Command -ComputerName <Target_Computer> -ScriptBlock { <Malicious_Command> }
