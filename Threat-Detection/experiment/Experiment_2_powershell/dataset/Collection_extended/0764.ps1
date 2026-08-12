# Natural language intent:
# Get users with reversible encryption (PWD in clear text with dcsync)

Get-DomainUser -Identity * | ? { $_.useraccountcontrol -like '*ENCRYPTED_TEXT_PWD_ALLOWED*' } | select samaccountname , useraccountcontrol
