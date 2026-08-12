# Natural language intent:
# Execute PsExec on a remote computer with specific service parameters.

Invoke-PsExec -ComputerName 192.168.50.200 -ServiceName Updater32 -ServiceEXE 'service.exe'
