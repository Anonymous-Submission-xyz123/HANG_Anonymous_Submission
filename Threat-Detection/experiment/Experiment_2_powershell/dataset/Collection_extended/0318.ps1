# Natural language intent:
# Set PowerShell ReadLine options to disable adding commands to the history.

Set-PSReadLineOption -AddToHistoryHandler { return $false }
