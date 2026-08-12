# Natural language intent:
# Download a file from a remote server using PowerShell.

(New-Object System.Net.WebClient).DownloadFile("${RemoteFile}", "${destinationPath}")
