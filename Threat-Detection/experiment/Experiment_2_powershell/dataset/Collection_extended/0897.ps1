# Natural language intent:
# Retrieving Credentials from Database Connection Strings, Scans for database connection strings in web application configuration files, which often contain credentials for database access.

Select-String -Path C:\inetpub\wwwroot\*.config -Pattern 'connectionString' -CaseSensitive
