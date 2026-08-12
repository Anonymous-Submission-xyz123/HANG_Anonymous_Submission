# Natural language intent:
# Retrieve the version of Internet Explorer from the registry

(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Internet Explorer').Version
