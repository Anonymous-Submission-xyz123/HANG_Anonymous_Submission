# Natural language intent:
# Attack SID History was designed to support migration scenarios, where a user would be moved from one domain to another. To preserve access to resources in the "old" domain, the user's previous SID would be added to the SID History of their new account. So when creating such a ticket, the SID of a privileged group (EAs, DAs, etc) in the parent domain can be added that will grant access to all resources in the parent.  This can be achieved using either a Golden or Diamond Ticket. Find the SID of a group of the other domain (for example "Domain Admins") is with:

Get-DomainGroup -Identity "Domain Admins" -Domain parent.io -Properties ObjectSid
