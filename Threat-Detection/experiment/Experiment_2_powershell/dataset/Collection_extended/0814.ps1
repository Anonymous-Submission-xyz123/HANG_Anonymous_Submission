# Natural language intent:
# Extracting Network Configuration, This command gathers network configuration details such as interface aliases, IPv4 and IPv6 addresses, and DNS server information.

Get-NetIPConfiguration | Select-Object -Property InterfaceAlias, IPv4Address, IPv6Address, DNServer
