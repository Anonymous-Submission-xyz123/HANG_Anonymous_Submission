# Natural language intent:
# Retrieve Active Directory users with specific account control flags and format the output table.

Get-ADUser -Filter 'useraccountcontrol -band 4194304' -Properties useraccountcontrol | Format-Table name
