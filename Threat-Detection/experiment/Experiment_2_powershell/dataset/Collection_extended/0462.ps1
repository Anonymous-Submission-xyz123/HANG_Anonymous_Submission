# Natural language intent:
# Define an excluded process and add it to Windows Defender preferences using PowerShell.

$excludedProcess = "${excluded_process}" ; Add-MpPreference -ExclusionProcess $excludedProcess
