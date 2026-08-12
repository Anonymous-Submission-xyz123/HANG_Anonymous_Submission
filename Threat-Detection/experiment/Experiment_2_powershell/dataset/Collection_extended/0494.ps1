# Natural language intent:
# Execute malicious code on a remote host using PowerShell.

Invoke-Command -ComputerName <remote_host> -ScriptBlock { <malicious_code> }
