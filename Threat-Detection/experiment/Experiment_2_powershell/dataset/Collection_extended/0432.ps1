# Natural language intent:
# Update the LastAccessTime of files in a specified path using PowerShell.

Get-ChildItem ${filePath} | % { $_.LastAccessTime = "${targetTime}" }
