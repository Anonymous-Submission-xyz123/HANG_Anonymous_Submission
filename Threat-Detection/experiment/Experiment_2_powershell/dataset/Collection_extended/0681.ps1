# Natural language intent:
# Enumerates the machines where a specific domain user/group is a member of a specific local group.

Get-DomainGPOUserLocalGroupMapping -LocalGroup Administrators | select ObjectName , GPODisplayName , ContainerName , ComputerName
