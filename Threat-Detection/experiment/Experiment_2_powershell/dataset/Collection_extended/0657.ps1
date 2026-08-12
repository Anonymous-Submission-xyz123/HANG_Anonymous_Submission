# Natural language intent:
# Create a new item (file) and then remove it, ignoring errors if any.

New-Item -Path ${log_file} -Force | Out-Null ; Remove-Item ${log_file} -Force -ErrorAction Ignore
