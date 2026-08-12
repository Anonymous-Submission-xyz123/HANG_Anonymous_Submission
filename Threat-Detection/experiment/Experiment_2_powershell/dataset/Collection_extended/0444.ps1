# Natural language intent:
# Copy a file from a network share to a local destination using PowerShell.

$source = "\\server\share\sospicious_file.exe" ;$destination = "C:\sospicious_file.exe" ;Copy-Item -Path $source -Destination $dest
