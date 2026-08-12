# Natural language intent:
# Run PowerShell with specific settings to execute a command stored in encoded form.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -Command "Invoke-Expression ([System.Text.Encoding]::Unicode.GetString([System]))"
