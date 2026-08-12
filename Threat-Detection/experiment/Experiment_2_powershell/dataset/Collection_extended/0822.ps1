# Natural language intent:
# SID History Abuse You could also abuse SID History across a forest trust.  If a user is migrated from one forest to another and SID Filtering is not enabled, it becomes possible to add a SID from the other forest, and this SID will be added to the user's token when authenticating across the trust.  As a reminder, you can get the signing key with

Invoke-Mimikatz -Command '"lsadump::trust /patch"' -ComputerName dc.domain.local
