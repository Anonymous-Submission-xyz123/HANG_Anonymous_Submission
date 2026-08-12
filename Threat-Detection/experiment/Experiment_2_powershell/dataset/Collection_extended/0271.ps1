# Natural language intent:
# Retrieve Group Policy Objects (GPOs) from the domain and append the output to a specified file.

Get-GPO -Domain $ENV:userdnsdomain ${gpo_param} >> ${gpoutput}
