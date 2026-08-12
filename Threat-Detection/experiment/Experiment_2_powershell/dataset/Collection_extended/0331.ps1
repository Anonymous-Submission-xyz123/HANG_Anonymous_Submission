# Natural language intent:
# Azure login and delete an AD user with specified user principal name.

az login ; $userprincipalname = "${userprincipalname}" ; az ad user delete --id $userprincipalname
