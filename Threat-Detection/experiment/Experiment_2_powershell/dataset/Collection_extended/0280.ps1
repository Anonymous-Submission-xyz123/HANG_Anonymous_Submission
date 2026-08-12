# Natural language intent:
# Retrieve the current active user name and append it to a text file.

[System.Environment]::UserName | Out-File -FilePath .\CurrentactiveUser.txt  ; $env:UserName | Out-File -FilePath .\CurrentactiveUser.txt -Append
