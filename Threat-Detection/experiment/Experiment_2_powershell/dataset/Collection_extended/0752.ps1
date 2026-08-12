# Natural language intent:
# Enumerating from inside the domain.This looks for SPNs that starts with MSSQL.Test connections with each one

Get-SQLInstanceDomain | Get-SQLConnectionTestThreaded -verbose
