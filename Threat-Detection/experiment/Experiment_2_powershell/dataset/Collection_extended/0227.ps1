# Natural language intent:
# Executes multiple commands to retrieve information about domain users and local group members.

net user /domain ; get-localgroupmember -group Users ; get-aduser -filter *
