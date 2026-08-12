# Natural language intent:
# Enumerating from the network without domain session, If you don't have a AD account, you can try to find MSSQL scanning via UDP

Get-Content c:\temp\computers.txt | Get-SQLInstanceScanUDP -Verbose -Threads 10
