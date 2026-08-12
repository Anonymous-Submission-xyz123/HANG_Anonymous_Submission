# Natural language intent:
# Execute a hidden PowerShell command

Invoke-Command -ComputerName <target> -ScriptBlock {powershell -nop -w hidden -c <command>}
