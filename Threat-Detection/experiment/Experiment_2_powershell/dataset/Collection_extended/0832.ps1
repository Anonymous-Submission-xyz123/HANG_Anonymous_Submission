# Natural language intent:
# Find any machine accounts in privileged groups

Get-DomainGroup -AdminCount | Get-DomainGroupMember -Recurse | ? { $_.MemberName -like '*$' }
