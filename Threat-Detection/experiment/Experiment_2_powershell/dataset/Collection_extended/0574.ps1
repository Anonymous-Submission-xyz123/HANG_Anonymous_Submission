# Natural language intent:
# Create minidump files for all running processes

Get-Process | Out-Minidump -DumpFilePath 'C:	emp'
