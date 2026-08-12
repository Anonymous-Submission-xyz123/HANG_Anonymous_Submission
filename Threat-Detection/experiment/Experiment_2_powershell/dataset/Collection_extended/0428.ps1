# Natural language intent:
# Run PowerShell to execute the Calculator application with elevated privileges.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -Command Start-Process -FilePath C:\Windows\System32\calc.exe -Verb RunAs
