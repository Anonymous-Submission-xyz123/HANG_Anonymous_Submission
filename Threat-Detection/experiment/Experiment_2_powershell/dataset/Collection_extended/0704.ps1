# Natural language intent:
# Extracting SSH Keys from User Directories, Searches for RSA private keys in the .ssh directories of all users, which can be used for unauthorized access to SSH servers.

Get-ChildItem -Path C:\Users\*\.ssh\id_rsa -Recurse
