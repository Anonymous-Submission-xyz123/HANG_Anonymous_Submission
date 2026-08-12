# Natural language intent:
# Create a new registry item to disable privacy experience during Windows Out-Of-Box Experience (OOBE).

New-ItemProperty "HKCU:\Software\Policies\Microsoft\Windows\OOBE" -Name DisablePrivacyExperience -PropertyType DWord -Value 1 -Force
