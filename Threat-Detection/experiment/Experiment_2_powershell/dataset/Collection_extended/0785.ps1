# Natural language intent:
# Rubeus.exe to generate and display the Kerberos Ticket Granting Ticket (TGT) hash for a specified computer account ("FAKECOMPUTER$") with the password "123456" in the "domain.local" domain. This operation is commonly performed in Kerberos ticket forging or password spraying attacks for lateral movement or privilege escalation.

.\Rubeus.exe hash /password:123456 /user:FAKECOMPUTER$ /domain:domain.local
