# Natural language intent:
# Perform DNS resolution by querying the specified volume of times (${query_volume}) for a randomly generated subdomain with the specified type (${query_type}) and domain (${domain}).

for($i=0; $i -le ${query_volume}; $i++) { Resolve-DnsName -type "${query_type}" "${subdomain}.$(Get-Random -Minimum 1 -Maximum 999999).${domain}" -QuickTimeout}
