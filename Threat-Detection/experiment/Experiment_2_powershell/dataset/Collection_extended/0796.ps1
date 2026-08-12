# Natural language intent:
# Enumerate permissions for GPOs where users with RIDs of > 1000 have some kind of modification/control rights

Get-DomainObjectAcl -LDAPFilter '(objectCategory=groupPolicyContainer)' | ? { ( $_.SecurityIdentifier -match '^S-1-5-.*-[1-9]\d{3,}$' ) -and ( $_.ActiveDirectoryRights -match 'WriteProperty|GenericAll|GenericWrite|WriteDacl|WriteOwner' ) } | select ObjectDN , ActiveDirectoryRights , SecurityIdentifier | fl
