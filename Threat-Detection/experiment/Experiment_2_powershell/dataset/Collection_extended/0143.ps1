# Natural language intent:
# Use nltest to retrieve information about the domain controller for the current user's domain.

nltest /dsgetdc:$env:USERDOMAIN
