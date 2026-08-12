# Natural language intent:
# Execute a PowerShell script stored on the local system

$FilePath = "C:\malicious_script.ps1"; Invoke-Expression -Command $FilePath
