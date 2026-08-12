# Natural language intent:
# Get users inside "Administrators" group. If there are groups inside of this grup, the -Recurse option will print the users inside the others groups also

Get-NetGroupMember -Identity "Administrators" -Recurse
