# Natural language intent:
# Retrieve and format information about the computer system using WMI

get-wmiobject win32_computersystem | fl model
