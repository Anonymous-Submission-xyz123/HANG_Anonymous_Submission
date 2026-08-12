# Natural language intent:
# Read content from a file and send it as a POST request to a specified IP address.

$content = Get-Content ${input_file} ; Invoke-WebRequest -Uri ${ip_address} -Method POST -Body $content
