# Natural language intent:
# Base64 Encoding for Command Obfuscation, Encodes a PowerShell command in Base64 to obfuscate it, making it less detectable by security tools.

$command = 'Get-Process'; $encodedCommand = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($command)); powershell.exe EncodedCommand $encodedCommand
