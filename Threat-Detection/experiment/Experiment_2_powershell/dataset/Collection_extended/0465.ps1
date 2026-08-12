# Natural language intent:
# Enable PowerShell remoting and run a command on the local computer using PowerShell.

Enable-PSRemoting -Force ; Invoke-Command -ComputerName $env:COMPUTERNAME -ScriptBlock {whoami}
