# Natural language intent:
# Set up port forwarding using netsh

netsh interface portproxy add v4tov4 listenport=${listenport} connectport=${connectport} connectaddress=${connectaddress}
