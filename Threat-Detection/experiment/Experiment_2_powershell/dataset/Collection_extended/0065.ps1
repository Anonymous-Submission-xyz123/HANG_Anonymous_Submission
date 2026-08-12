# Natural language intent:
# Retrieve information about Active Directory replication accounts on a specific server.

Get-ADReplAccount -All -Server ${logonserver}
