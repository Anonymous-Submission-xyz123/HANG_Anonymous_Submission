# Natural language intent:
# Get info about the external forest (if possible)

Get-ForestGlobalCatalog -Forest external.domain ; Get-DomainTrust -SearchBase "GC://$($ENV:USERDNSDOMAIN)"
