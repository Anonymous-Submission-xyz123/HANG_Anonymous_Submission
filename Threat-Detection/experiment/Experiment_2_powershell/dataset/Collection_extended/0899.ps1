# Natural language intent:
# To stop a guest SMB shared drive, (This could come handy for transferring files, exfiltration etc.) execute:

Remove-SmbShare -Name "sharedir" -Force
