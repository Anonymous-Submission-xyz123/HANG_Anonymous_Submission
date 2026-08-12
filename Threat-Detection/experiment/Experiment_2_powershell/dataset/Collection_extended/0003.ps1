# Natural language intent:
# Connect to Azure AD, retrieve the user principal name, and remove the corresponding user.

Connect-AzureAD ; $userprincipalname = "${userprincipalname}" ; Remove-AzureADUser -ObjectId $userprincipalname
