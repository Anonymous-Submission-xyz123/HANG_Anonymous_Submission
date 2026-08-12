# Natural language intent:
# Search for domain objects in the specified domain with a custom LDAP filter and retrieve specific properties.

Get-DomainSearcher -Domain testlab.local -LDAPFilter '(samAccountType=805306368)' -Properties 'SamAccountName,lastlogon'
