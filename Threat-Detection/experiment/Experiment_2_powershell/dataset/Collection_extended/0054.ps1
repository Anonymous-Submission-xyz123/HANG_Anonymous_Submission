# Natural language intent:
# Execute custom PowerShell code on a remote host.

Invoke-Command -ComputerName <remote_host> -ScriptBlock { < code > }
