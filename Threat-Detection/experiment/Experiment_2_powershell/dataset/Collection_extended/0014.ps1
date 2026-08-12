# Natural language intent:
# Set a file path and execute the corresponding PowerShell script.

$FilePath = "C:\payload.ps1"; Invoke-Expression -Command $FilePath
