# Natural language intent:
# Create a new Windows service with a specified name and binary path, then start the service.

New-Service -Name "${ServiceName}" -BinaryPathName "${BinaryPath}" ; Start-Service -Name "${ServiceName}"
