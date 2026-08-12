# Natural language intent:
# Disable User Account Control (UAC) by setting the EnableLUA registry key to 0.

New-ItemProperty -Path HKLM:Software\Microsoft\Windows\CurrentVersion\policies\system -Name EnableLUA -PropertyType DWord -Value 0 -Force
