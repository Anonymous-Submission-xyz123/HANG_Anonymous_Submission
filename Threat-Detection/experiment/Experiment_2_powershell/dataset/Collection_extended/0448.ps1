# Natural language intent:
# Change location to a specified path and run accesschk.exe with specific parameters using PowerShell.

Set-Location -path "${file_path}\Sysinternals"; ; ./accesschk.exe -accepteula .;
