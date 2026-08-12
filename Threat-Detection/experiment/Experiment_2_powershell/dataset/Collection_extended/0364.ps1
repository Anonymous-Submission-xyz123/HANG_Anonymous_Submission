# Natural language intent:
# Create a new item property in the registry with specified options.

New-ItemProperty -Path HKLM:\SYSTEM\CurrentControlSet\Services ; TDS -Name LsaDbExtPt -Value "${dll_path}"
