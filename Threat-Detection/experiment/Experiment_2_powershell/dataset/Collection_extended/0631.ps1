# Natural language intent:
# Retrieve information about processes, copy to clipboard, and execute from clipboard.

echo Get-Process | clip ; Get-Clipboard | iex
