# Natural language intent:
# Search for SNMP community string in registry, Finding a SNMP community string is not a critical issue, but it could be useful to Understand what kind of password patterns are used among sysadmins in the organization, The following command will extract SNMP community string stored in the registry, if there is any:

gci HKLM:\SYSTEM\CurrentControlSet\Services\SNMP -Recurse -EA SilentlyContinue
