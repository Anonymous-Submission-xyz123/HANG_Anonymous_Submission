# Natural language intent:
# Invoke a command with a potentially malicious script block on a target machine.

Invoke-Command -ComputerName <target_machine> -ScriptBlock { <bad_code> }
