# Natural language intent:
# Define a command to execute the Calculator and execute it using PowerShell Invoke-Expression.

$cmd = "C:\Windows\System32\cmd.exe /c calc.exe";Invoke-Expression -Command $cmd;
