# Natural language intent:
# Encrypt a file using GPG with specified GPG executable and file locations.

cmd /c '${GPG_Exe_Location}' -c '${File_to_Encrypt_Location}'
