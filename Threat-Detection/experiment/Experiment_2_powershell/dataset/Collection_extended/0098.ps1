# Natural language intent:
# Copy Microsoft Edge user data to a temporary folder.

Copy-Item "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default" -Destination $env:temp\Edge -Force -Recurse
