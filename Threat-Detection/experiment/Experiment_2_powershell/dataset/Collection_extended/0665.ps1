# Natural language intent:
# Perform an LDAP search in the specified domain for user accounts with a specific account type and retrieve selected properties.

Get-DomainSearcher -Domain Pedrolprova.local -LDAPFilter '(samAccountType=805306368)' -Properties 'SamAccountName,lastlogon'
