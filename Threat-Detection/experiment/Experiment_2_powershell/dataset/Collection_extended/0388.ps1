# Natural language intent:
# Map a network drive using specified domain credentials.

net use \\${remote.host.fqdn}\C$ /user:${dom.user.name} ${dom.user.pwd}
