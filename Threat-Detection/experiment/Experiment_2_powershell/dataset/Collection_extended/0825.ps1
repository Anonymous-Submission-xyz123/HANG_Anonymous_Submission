# Natural language intent:
# Abuse Organizations can check if the setting is enabled using the following `certutil.exe` command.

certutil -config "CA_HOST\CA_NAME" -getreg "policy\EditFlags"
