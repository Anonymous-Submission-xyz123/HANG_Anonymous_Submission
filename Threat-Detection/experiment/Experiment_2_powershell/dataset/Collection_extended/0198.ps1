# Natural language intent:
# Invokes a command (payload) on a remote computer.

Invoke-Command -ComputerName <target> -ScriptBlock { <payload> }
