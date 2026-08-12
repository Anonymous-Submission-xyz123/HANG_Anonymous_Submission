# Natural language intent:
# Encoded Command Execution, Executes a Base64-encoded PowerShell command, which can help bypass simple command-line logging and analysis tools.

$encodedCmd = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes('Get-Process')); powershell.exe -EncodedCommand $encodedCmd
