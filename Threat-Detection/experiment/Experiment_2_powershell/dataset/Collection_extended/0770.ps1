# Natural language intent:
# Executing Remote Commands, Executes a command remotely on a target PC, in this case, listing processes. Requires credentials for the target system.

Invoke-Command -ComputerName TargetPC -ScriptBlock { Get-Process } -Credential (Get-Credential)
