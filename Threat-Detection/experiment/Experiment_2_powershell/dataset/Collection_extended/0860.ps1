# Natural language intent:
# Get usernames and their groups where name is like "admin"

Get-DomainGroup | where Name -like "*Admin*" | select samaccountname
