# Natural language intent:
# Get-DomainObject cmdlet to retrieve information about the machine account quota for the domain specified as "domain.local." The command fetches the machine account quota attribute for the domain "dc=domain,dc=local" and then selects and displays the "MachineAccountQuota" property. This information is related to the limit on the number of computer objects (machine accounts) that can be created in the specified domain.

Get-DomainObject -Identity "dc=domain,dc=local" -Domain domain.local | select MachineAccountQuota
