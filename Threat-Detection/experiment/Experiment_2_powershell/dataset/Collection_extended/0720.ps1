# Natural language intent:
# System Information with WMI.

Get-WmiObject -ClassName win32_operatingsystem | select * | more
