# Natural language intent:
# Create a new registry item to run a specified command automatically.

New-ItemProperty -Path "HKLM:\Software\Microsoft\Command Processor" -Name "AutoRun" -Value "${cmd}" -PropertyType "String"
