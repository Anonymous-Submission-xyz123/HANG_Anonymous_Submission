# Natural language intent:
# Try to connect and obtain info from each MSSQL server (also useful to check conectivity)

Get-SQLInstanceDomain | Get-SQLServerInfo -Verbose
