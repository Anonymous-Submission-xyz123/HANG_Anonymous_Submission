# Natural language intent:
# Change expiration time of the password

Set-DomainObject -Identity wkstn-2 -Set @{ "ms-mcs-admpwdexpirationtime" = "232609935231523081" }
