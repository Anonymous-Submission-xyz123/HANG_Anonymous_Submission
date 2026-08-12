# Natural language intent:
# Access DB Search keywords in columns trying to access the MSSQL DBs

Get-SQLInstanceDomain | Get-SQLConnectionTest | ? { $_.Status -eq "Accessible" } | Get-SQLColumnSampleDataThreaded -Keywords "password" -SampleSize 5 | select instance , database , column , sample | ft -autosize
