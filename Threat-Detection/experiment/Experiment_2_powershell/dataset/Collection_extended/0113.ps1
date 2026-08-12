# Natural language intent:
# Execute PowerShell code with hidden window, no profile, and loading code from the file WinPwn.ps1.

powershell -w hidden -nop -c $x=(gc c:\WinPwn.ps1);iex $x
