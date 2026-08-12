# Natural language intent:
# Map a network drive using specified credentials.

net use \\${remote.host.fqdn}\C$ /user:${domain.user.name} ${domain.user.password}
