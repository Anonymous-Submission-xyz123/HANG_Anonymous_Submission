# Natural language intent:
# Get usernames and their groups

Get-DomainUser -Properties name , MemberOf | fl
