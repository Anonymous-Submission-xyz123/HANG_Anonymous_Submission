# Natural language intent:
# Download a file from a remote server using PowerShell.

(New-Object System.Net.WebClient).DownloadFile("${remote_file}", "${destination_path}")
