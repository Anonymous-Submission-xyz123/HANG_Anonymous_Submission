# Natural language intent:
# Create a new registry item to disable Command Prompt using PowerShell.

New-ItemProperty -Path "HKCU:\Software\Policies\Microsoft\Windows\System" -Name DisableCMD -Value 1
