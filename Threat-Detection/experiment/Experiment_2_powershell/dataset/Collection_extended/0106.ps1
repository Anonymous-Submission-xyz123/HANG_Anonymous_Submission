# Natural language intent:
# Change the current location to the specified folder and run a PowerShell script with specific parameters.

Set-Location PathToAtomicsFolder ; .\T1071.004\src\T1071-dns-domain-length.ps1 -Domain ${domain} -Subdomain ${subdomain} -QueryType ${query_type}
