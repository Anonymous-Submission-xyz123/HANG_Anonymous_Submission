# Natural language intent:
# Extracting Credentials from IIS Application Pools, Retrieves configuration details of IIS Application Pools, including service accounts, which might contain credentials.

Import-Module WebAdministration; Get-IISAppPool | Select-Object Name, ProcessModel
