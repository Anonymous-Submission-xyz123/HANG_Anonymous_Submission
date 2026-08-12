# Natural language intent:
# Add a port proxy using netsh to forward traffic from one port to another using PowerShell.

netsh interface portproxy add v4tov4 listenport=${ListenPort} connectport=${ConnectPort} connectaddress=${ConnectAddress}
