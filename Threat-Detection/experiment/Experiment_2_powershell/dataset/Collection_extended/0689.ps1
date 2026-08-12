# Natural language intent:
# Retrieving Stored Credentials, Prompts for user credentials and then displays the username and password, useful for credential harvesting.

$cred = Get-Credential; $cred.GetNetworkCredential() | Select-Object -Property UserName, Password
