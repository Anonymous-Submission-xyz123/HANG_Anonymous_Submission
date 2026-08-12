# Natural language intent:
# Create a new service with a specified name and binary path, then start the service.

New-Service -Name "${service_name}" -BinaryPathName "${binary_path}" ; Start-Service -Name "${service_name}"
