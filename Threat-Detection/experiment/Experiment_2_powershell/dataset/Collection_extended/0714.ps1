# Natural language intent:
# Find potentially interesting files, With this command we can identify files with potentially sensitive data such as account information, credentials, configuration files etc. based on their filename:

gci c:\ -Include *pass*.txt,*pass*.xml,*pass*.ini,*pass*.xlsx,*cred*,*vnc*,*.config*,*accounts* -File -Recurse -EA SilentlyContinue
