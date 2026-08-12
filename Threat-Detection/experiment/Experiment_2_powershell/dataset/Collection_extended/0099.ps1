# Natural language intent:
# Modify the creation time of files in the specified path to the target date and time.

Get-ChildItem ${file_path} | % { $_.CreationTime = "${target_date_time}" }
