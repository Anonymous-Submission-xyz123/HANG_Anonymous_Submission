# Natural language intent:
# Download content from the specified URL into ${Output_File} and open it using Invoke-Item.

(New-Object Net.WebClient).DownloadString('${TRF}') | Out-File ${Output_File}; Invoke-Item ${Output_File}
