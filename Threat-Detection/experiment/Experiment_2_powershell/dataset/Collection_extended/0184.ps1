# Natural language intent:
# Adds a firewall rule to open a specified TCP port.

netsh advfirewall firewall add rule name="Opens Port to Any" dir=in protocol=tcp localport=${port} action=allow profile=any
