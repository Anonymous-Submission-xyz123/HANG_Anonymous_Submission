# Natural language intent:
# Invoke a command on a remote server to start a process with the specified file path.

Invoke-Command -ComputerName [RemoteServer] -ScriptBlock { Start-Process -FilePath "C:\malware.exe" }
