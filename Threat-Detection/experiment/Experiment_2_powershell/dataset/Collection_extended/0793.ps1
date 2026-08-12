# Natural language intent:
# Get special rights over All administrators in domain

Get-NetGroupMember -GroupName "Administrators" -Recurse | ? { $_.IsGroup -match "false" } | % { Get-ObjectACL -SamAccountName $_.MemberName -ResolveGUIDs } | select ObjectDN , IdentityReference , ActiveDirectoryRights
