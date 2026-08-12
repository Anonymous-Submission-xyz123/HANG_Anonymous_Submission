# Natural language intent:
# Invoke a method on a WMI class (Win32_Product) with specified arguments

Invoke-CimMethod -ClassName Win32_Product -MethodName ${action} -Arguments @{ PackageLocation = '${MSI_p}' }
