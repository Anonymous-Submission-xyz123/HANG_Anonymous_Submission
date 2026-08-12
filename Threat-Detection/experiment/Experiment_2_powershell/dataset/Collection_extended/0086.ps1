# Natural language intent:
# Execute a malicious PowerShell script with execution policy bypass and a hidden window.

powershell.exe -executionpolicy bypass -noprofile -windowstyle hidden -file malicious.ps1
