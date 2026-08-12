# Natural language intent:
# Returns all GPOs that modify local group memberships through Restricted Groups or Group Policy Preferences.

Get-DomainGPOLocalGroup | select GPODisplayName , GroupName , GPOType
