# Natural language intent:
# Check if any of the interesting permissions founds is realated to a username/group

Find-InterestingDomainAcl -ResolveGUIDs | ? { $_.IdentityReference -match "RDPUsers" }
