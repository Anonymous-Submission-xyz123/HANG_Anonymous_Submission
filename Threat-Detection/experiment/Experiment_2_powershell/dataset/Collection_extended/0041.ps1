# Natural language intent:
# Execute malicious code on a remote system using PowerShell remoting.

Invoke-Command -ComputerName <TargetSystem> -ScriptBlock {< maliciouscode >}
