# Natural language intent:
# Invoke PsExec to run a command on a remote computer with specified options.

Invoke-PsExec -ComputerName 192.168.50.200 -Command 'dir C:\' -ServiceName Updater32 -ResultFile 'results.txt'
