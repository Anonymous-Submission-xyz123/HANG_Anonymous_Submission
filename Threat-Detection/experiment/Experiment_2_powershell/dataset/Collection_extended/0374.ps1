# Natural language intent:
# Invoke a potentially malicious command on a target computer.

Invoke-Command -ComputerName [TARGET_IP] -ScriptBlock {[BAD_COMMAND]}
