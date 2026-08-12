# Natural language intent:
# Stop and remove a specified service by name.

Stop-Service -Name ${service_name} ; Remove-Service -Name ${service_name}
