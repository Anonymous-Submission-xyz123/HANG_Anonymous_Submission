# Natural language intent:
# Creates a new item at the specified path and removes an item, potentially related to TeamViewer log files.

New-Item -Path ${teamviewer_log_file} -Force | Out-Null ; Remove-Item ${teamviewer_log_file} -Force -ErrorAction Ignore
