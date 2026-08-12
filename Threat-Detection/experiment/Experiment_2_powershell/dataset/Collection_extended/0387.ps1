# Natural language intent:
# Create a new item property in the Windows Registry with specified options.

New-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name T1112 -Value "<script>"
