# Natural language intent:
# Retrieve group memberships for a specified Active Directory user.

get-ADPrincipalGroupMembership ${user} | select name
