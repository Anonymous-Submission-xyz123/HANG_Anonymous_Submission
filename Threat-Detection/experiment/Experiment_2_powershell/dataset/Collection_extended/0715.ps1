# Natural language intent:
# Dumping Credentials from Windows Services, Lists Windows services that are running under a specific user account, which can sometimes include credentials in the service configuration.

Get-WmiObject win32_service | Where-Object {$_.StartName -like '*@*'} | Select-Object Name, StartName, DisplayName
