# Natural language intent:
# Invoke DCOM to execute the 'calc.exe' command on a remote computer using the MMC20.Application method.

Invoke-DCOM -ComputerName '192.168.2.100' -Method MMC20.Application -Command 'calc.exe'
