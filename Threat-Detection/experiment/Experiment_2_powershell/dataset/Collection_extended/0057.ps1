# Natural language intent:
# Create a minidump file for the process with ID 2929.

Out-Minidump -Process (Get-Process -Id 2929)
