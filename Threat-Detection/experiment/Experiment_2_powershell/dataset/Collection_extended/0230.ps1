# Natural language intent:
# Retrieves information about directory service computers using WMI.

get-wmiobject -class ds_computer -namespace root\directory\ldap
