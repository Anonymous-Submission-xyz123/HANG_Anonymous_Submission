# Natural language intent:
# Update the LastWriteTime of files in a specified path using PowerShell.

Get-ChildItem ${File_Path} | % { $_.LastWriteTime = "${Date_time}" }
