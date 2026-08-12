# Natural language intent:
# Execute an illegal command on a remote host using PowerShell.

Invoke-Command -ComputerName <remote_host> -ScriptBlock { <illegal_command> }
