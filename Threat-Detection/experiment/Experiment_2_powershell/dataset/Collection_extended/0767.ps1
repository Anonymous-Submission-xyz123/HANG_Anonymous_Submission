# Natural language intent:
# Enumerating Domain Users, Retrieves a list of all domain users, including their names, account status, and last logon dates.

Get-ADUser -Filter * -Properties * | Select-Object -Property Name, Enabled, LastLogonDate
