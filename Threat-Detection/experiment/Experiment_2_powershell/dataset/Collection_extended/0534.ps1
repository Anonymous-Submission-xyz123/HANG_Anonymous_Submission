# Natural language intent:
# Retrieve information about the current Windows identity and save it to a file.

[System.Security.Principal.WindowsIdentity]::GetCurrent() | Out-File -FilePath .\CurrentUserObject.txt
