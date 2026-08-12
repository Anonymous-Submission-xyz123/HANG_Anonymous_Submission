# Natural language intent:
# Get Active Directory objects using a specified LDAP filter and server.

Get-ADObject -LDAPFilter '(UserAccountControl:1.2.840.113556.1.4.803:=${uac_prop})' -Server ${domain}
