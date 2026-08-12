# Natural language intent:
# Invokes a CIM method on the Win32_Product class with specific arguments.

Invoke-CimMethod -ClassName Win32_Product -MethodName ${action} -Arguments @{ PackageLocation = '${MSIPayload}' }
