# Natural language intent:
# Add-ObjectAcl cmdlet to grant the DCSync rights to a specified user ("username") on the Active Directory object with the distinguished name "dc=dollarcorp,dc=moneycorp,dc=local". This command is essentially configuring permissions to allow the specified user to perform DCSync operations on the specified Active Directory object.

Add-ObjectAcl -TargetDistinguishedName "dc=dollarcorp,dc=moneycorp,dc=local" -PrincipalSamAccountName username -Rights DCSync -Verbose
