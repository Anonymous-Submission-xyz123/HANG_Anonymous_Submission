# Natural language intent:
# Allow Remote Desktop connections, Allow RDP connections

(Get-WmiObject -Class "Win32_TerminalServiceSetting" -Namespace root\cimv2\terminalservices).SetAllowTsConnections(1)
