# Natural language intent:
# Find computers with Constrained Delegation

Get-NetComputer -TrustedToAuth | select samaccountname
