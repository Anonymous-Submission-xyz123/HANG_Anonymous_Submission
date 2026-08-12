# Natural language intent:
# Find interesting ACLs

Invoke-ACLScanner -ResolveGUIDs | select IdentityReferenceName , ObjectDN , ActiveDirectoryRights | fl
