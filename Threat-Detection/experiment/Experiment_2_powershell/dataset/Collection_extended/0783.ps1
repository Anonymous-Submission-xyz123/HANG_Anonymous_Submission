# Natural language intent:
# Add user to 'Domain Admins'

Add-NetGroupUser -Username username -GroupName 'Domain Admins' -Domain my.domain.local
