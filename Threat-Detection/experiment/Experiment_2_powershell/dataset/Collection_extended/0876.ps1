# Natural language intent:
# Find database credentials in configuration files, Using the following PowerShell command we can find database connection strings (with plaintext credentials) stored in various configuration files such as web.config for ASP.NET configuration, in Visual Studio project files etc.:

gci c:\ -Include *.config,*.conf,*.xml -File -Recurse -EA SilentlyContinue | Select-String -Pattern "connectionString"
