# Natural language intent:
# Retrieve Group Policy Objects

Get-GPO -Domain $ENV:userdnsdomain ${gpo_p} >> ${gpo_out}
