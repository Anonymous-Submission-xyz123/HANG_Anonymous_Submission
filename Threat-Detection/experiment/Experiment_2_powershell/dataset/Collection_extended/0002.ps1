# Natural language intent:
# Execute a command on a remote host using PowerShell remoting.

Invoke-Command -ComputerName <remote_host> -ScriptBlock { <command> }
