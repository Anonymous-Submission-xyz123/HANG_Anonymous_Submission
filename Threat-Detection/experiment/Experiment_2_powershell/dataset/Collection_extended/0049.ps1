# Natural language intent:
# Create a new registry item to disable Event Tracing for Windows (ETW).

New-ItemProperty -Path HKLM:\Software\Microsoft\.NETFramework -Name ETWEnabled -Value 0 -PropertyType "DWord" -Force
