# Natural language intent:
# Reading Credentials from Configuration Files, Searches for strings containing `password=' in all .config files on the C: drive, which can reveal hardcoded credentials.

Get-ChildItem -Path C:\ -Include *.config -Recurse | Select-String -Pattern 'password='
