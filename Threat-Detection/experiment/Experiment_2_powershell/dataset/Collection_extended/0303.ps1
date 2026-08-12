# Natural language intent:
# Retrieve Active Directory users who do not require pre-authentication.

get-aduser -f * -pr DoesNotRequirePreAuth | where {$_.DoesNotRequirePreAuth -eq $TRUE}
