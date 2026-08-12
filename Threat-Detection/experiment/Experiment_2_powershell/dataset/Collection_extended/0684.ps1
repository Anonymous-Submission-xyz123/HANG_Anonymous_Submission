# Natural language intent:
# This is for an attack from child to root domain, Get child domain SID (this is the SID of the domain that has the trust relationship with the root domain)

lookupsid.py < child_domain>/username@10.10.10.10 | grep "Domain SID"
