# Natural language intent:
# Port scan a network for a single port (port-sweep) with PowerShell TcpClient, This could be useful for example for quickly discovering SSH interfaces (port tcp/22) on a specified network Class C subnet (10.10.0.0/24):

$port = 22;$net = "10.10.0.";0..255 | foreach { echo ((new-object Net.Sockets.TcpClient).Connect($net+$_,$port)) "Port $port is open on $net$_"} 2>$null
