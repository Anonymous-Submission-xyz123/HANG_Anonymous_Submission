# Natural language intent:
# Create a minidump of a specified process with ID 5121.

Out-Minidump -Process (Get-Process -Id 5121)
