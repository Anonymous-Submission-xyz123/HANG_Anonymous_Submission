# Natural language intent:
# Invoke the execution of a command using PowerShell's Invoke-Expression, running a potentially malicious file located at 'C:\Windows\temp\bad_file.exe'.

Invoke-Expression -Command "& {C:\Windows\temp\bad_file.exe}"
