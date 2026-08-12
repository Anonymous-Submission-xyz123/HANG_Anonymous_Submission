# Natural language intent:
# Get root domain SID (this is the SID of the domain that has the trust relationship with the child domain)

lookupsid.py < child_domain>/username@10.10.10.10 | grep -B20 "Enterprise Admins" | grep "Domain SID"
