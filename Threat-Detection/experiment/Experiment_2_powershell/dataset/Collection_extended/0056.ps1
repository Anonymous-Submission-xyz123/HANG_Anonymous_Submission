# Natural language intent:
# Modify Windows Defender settings to disable anti-spyware features.

Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender" -Name DisableAntiSpyware -Value 1
