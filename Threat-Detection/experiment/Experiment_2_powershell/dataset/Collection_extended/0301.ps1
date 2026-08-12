# Natural language intent:
# Create a new registry property to disable the operational log for Windows Defender.

New-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\WINEVT\Channels\Microsoft-Windows-Windows Defender" -Name Operational  -PropertyType DWord -Value 0 -Force
