# Natural language intent:
# Decodes and executes a Base64-encoded PowerShell command.

powershell.exe -c "Invoke-Expression ([System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('base64 encoded string')))"
