# Natural language intent:
# Send a POST request to a specified IP address with the content of the specified input file.

Invoke-WebRequest -Uri ${ipAddress} -Method POST -Body ${INPUT_file}
