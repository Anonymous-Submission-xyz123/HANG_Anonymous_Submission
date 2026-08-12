# Natural language intent:
# Removes an item specified by the path after joining with the result of a command that retrieves the first item in the prefetch directory.

Remove-Item -Path (Join-Path "$Env:SystemRoot\prefetch" (Get-ChildItem -Path "$Env:SystemRoot\prefetch*.pf" -Name)[0])
