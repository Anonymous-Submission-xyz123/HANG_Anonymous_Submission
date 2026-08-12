# Natural language intent:
# Execute a malicious PowerShell script located at C:\malicious_script.ps1 with bypassing execution policy and without loading user profiles.

powershell.exe -ExecutionPolicy Bypass -NoProfile -File C:\malicious_script.ps1
