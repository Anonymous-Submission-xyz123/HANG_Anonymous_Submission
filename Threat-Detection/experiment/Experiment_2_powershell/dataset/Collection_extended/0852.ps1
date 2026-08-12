# Natural language intent:
# Check for LSASS WDigest caching, Using the following command we can check whether the WDigest credential caching is enabled on the system or not. This settings dictates whether we will be able to use Mimikatz to extract plaintext credentials from the LSASS process memory.

(gp registry::HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\Wdigest).UseLogonCredential
