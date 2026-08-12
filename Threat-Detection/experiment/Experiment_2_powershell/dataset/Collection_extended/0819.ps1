# Natural language intent:
# List all usernames

Get-NetUser | select samaccountname , description , pwdlastset , logoncount , badpwdcount
