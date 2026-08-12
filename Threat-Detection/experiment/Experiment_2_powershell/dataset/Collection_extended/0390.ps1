# Natural language intent:
# Retrieve Group Policy Objects (GPOs) in the specified domain and append the results to a file.

Get-GPO -Domain $ENV:userdnsdomain ${gpo_param} >> ${gpo_output}
