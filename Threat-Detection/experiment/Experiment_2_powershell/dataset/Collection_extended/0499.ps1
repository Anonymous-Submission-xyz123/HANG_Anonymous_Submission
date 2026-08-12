# Natural language intent:
# Run malicious code on a specified remote target using PowerShell.

Invoke-Command -ComputerName <target> -ScriptBlock { <malicious code > }
