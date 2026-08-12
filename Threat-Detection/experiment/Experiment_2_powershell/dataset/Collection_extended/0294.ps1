# Natural language intent:
# Set the location to the specified folder, then execute a PowerShell script related to T1071.004 with specific parameters.

Set-Location PathToAtomicsFolder ; .\T1071.004\src\T1071-dns-domain-length.ps1 -Domain ${dom} -Subdomain ${subd} -QueryType ${QueryType}
