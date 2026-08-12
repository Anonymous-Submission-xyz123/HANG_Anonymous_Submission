# Natural language intent:
# Perform DNS resolutions in a loop with random subdomains.

for($i=0; $i -le ${query_volume}; $i++) { Resolve-DnsName -type "${queryType}" "${Subdomain}.$(Get-Random -Minimum 1 -Maximum 999999).${Domain}" -QuickTimeout}
