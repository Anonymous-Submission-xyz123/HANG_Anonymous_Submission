# Natural language intent:
# Test the network connection to a specified domain and port.

Test-NetConnection -ComputerName ${domain} -port ${port}
