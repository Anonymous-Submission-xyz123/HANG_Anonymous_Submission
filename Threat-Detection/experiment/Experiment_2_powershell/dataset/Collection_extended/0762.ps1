# Natural language intent:
# Get Kerberoastable users

setspn.exe -Q */* ; Get-NetUser -SPN | select serviceprincipalname
