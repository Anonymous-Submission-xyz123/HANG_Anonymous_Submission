# Natural language intent:
# Command Aliasing, Creates an alias for a PowerShell command to disguise its true purpose, which can be useful in evading script analysis.

$alias = 'Get-Dir'; Set-Alias -Name $alias -Value Get-ChildItem; Invoke-Expression $alias
