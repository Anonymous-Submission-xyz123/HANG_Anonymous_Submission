# Natural language intent:
# Executes multiple commands using cmd.exe, appending results to a history log file.

cmd.exe /c "net user" >> C:\Windows\temp\history.log; ; cmd.exe /c "whoami /priv" >> C:\Windows\temp\history.log; ; cmd.exe /c "netstat -ano" >> C:\Windows\temp\history.log
