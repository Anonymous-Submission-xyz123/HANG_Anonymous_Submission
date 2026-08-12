# Natural language intent:
# Start PowerShell and run a script with specified arguments to emulate administrator tasks.

start powershell.exe -ArgumentList "-NoP","-StA","-ExecutionPolicy","bypass",".\Emulate-Administrator-Tasks.ps1"
