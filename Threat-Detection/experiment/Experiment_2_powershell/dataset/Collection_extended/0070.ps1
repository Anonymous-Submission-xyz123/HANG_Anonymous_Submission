# Natural language intent:
# Map a new PowerShell drive to a specified network share.

New-PSDrive -name ${map_name} -psprovider filesystem -root \\${computer_name}\${share_name}
