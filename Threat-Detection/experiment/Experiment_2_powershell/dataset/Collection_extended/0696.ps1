# Natural language intent:
# If you have some valid credentials and you have discovered valid MSSQL hosts you can try to login into them. The discovered MSSQL servers must be on the file: C:\temp\instances.txt

Get-SQLInstanceFile -FilePath C:\temp\instances.txt | Get-SQLConnectionTest -Verbose -Username test -Password test
