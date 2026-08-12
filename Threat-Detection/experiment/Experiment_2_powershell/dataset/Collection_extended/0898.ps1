# Natural language intent:
# Basic user enabled info

Get-NetUser -UACFilter NOT_ACCOUNTDISABLE | select samaccountname , description , pwdlastset , logoncount , badpwdcount
