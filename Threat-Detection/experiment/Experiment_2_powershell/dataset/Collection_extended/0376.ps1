# Natural language intent:
# Invoke a command on a target computer with a potentially malicious encoded command.

Invoke-Command -ComputerName <target> -ScriptBlock { Start-Process powershell.exe -ArgumentList '-NoP -NonI -W Hidden -Enc <encoded_command>' }
