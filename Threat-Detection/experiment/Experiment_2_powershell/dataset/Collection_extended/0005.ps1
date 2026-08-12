# Natural language intent:
# Execute a PowerShell script with bypassing execution policy and hiding the window.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -File bad_script.ps1
