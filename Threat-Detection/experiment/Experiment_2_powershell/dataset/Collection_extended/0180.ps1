# Natural language intent:
# Removes the history file associated with the PSReadline module.

Remove-Item (Get-PSReadlineOption).HistorySavePath
