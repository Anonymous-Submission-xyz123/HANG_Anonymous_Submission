# Natural language intent:
# Execute a local PowerShell script

$scriptPath = 'C:\malicious_script.ps1'; Invoke-Expression -Command $scriptPath
