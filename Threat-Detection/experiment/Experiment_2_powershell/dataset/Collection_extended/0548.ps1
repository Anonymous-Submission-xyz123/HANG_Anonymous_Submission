# Natural language intent:
# Invoke DCOM to start a specified service on a remote computer.

Invoke-DCOM -ComputerName '192.168.2.100' -Method ServiceStart 'MyService'
