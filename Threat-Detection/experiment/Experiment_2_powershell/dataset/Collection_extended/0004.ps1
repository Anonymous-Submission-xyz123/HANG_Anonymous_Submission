# Natural language intent:
# Create a minidump file for the process with ID 3742.

Out-Minidump -Process (Get-Process -Id 3742)
