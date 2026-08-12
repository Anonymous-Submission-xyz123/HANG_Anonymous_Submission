# Natural language intent:
# Executes a PowerShell script located at "C:\evilFail.ps1" with specific execution policies.

powershell.exe -ExecutionPolicy Bypass -NoProfile -File C:\evilFail.ps1
