# Natural language intent:
# Execute PowerShell with a hidden window and bypass execution policy to run malicious code.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -WindowStyle Hidden -EncodedCommand [Base64 encoded malicious code]
