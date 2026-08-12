# Natural language intent:
# Add a firewall rule to open a specified TCP port for incoming traffic.

netsh advfirewall firewall add rule name="Open Port to Any" dir=in protocol=tcp localport=${local_port} action=allow profile=any
