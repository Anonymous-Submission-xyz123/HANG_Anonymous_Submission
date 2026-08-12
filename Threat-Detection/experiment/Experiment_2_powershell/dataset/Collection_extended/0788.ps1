# Natural language intent:
# Check if AlwaysInstallElevated is enabled, If the following AlwaysInstallElevated registry keys are set to 1, it means that any low privileged user can install *.msi files with NT AUTHORITY\SYSTEM privileges. Here's how to check it with PowerShell:

gp 'HKCU:\Software\Policies\Microsoft\Windows\Installer' -Name AlwaysInstallElevated;gp 'HKLM:\Software\Policies\Microsoft\Windows\Installer' -Name AlwaysInstallElevated
