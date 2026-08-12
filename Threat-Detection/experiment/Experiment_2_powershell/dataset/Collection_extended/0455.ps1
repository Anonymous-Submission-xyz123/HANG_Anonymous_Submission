# Natural language intent:
# Invoke a command to retrieve process information and save it to a file using PowerShell.

Invoke-Expression -Command "Get-Process | Out-File -Encoding ASCII C:\malicious.txt"
