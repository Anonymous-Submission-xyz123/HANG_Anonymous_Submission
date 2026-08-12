# Natural language intent:
# Remove a SMB share and a file share with specified names.

Remove-SmbShare -Name ${share_name} ; Remove-FileShare -Name ${share_name}
