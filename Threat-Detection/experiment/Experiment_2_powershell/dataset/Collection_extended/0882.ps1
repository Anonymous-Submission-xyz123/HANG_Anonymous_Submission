# Natural language intent:
# Here's a useful command to whitelist an IP address in the Windows firewall, after this we should be able to connect to this host from our IP address (10.10.15.123) on every port:

New-NetFirewallRule -Action Allow -DisplayName "pentest" -RemoteAddress 10.10.15.123
