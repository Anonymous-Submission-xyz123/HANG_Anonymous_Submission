# Natural language intent:
# Bypassing Execution Policy for Script Execution, Temporarily bypasses the script execution policy to run a PowerShell script, allowing execution of unsigned scripts.

Set-ExecutionPolicy Bypass -Scope Process -Force; .\script.ps1
