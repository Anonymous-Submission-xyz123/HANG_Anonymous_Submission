# Natural language intent:
# Process Information with WMI.

Get-WmiObject win32_process | Select Name, Processid
