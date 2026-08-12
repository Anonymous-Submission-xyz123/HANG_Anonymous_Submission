# Natural language intent:
# Retrieving Passwords from Unsecured Files, Searches for the term `password' in all text files within the Documents folders of all users, which can reveal passwords stored insecurely.

Select-String -Path C:\Users\*\Documents\*.txt -Pattern 'password' -CaseSensitive
