# Natural language intent:
# Read content from a file and send it as a POST request to a specified IP address using PowerShell.

$content = Get-Content ${InputFile} ; Invoke-WebRequest -Uri ${Ip_Address} -Method POST -Body $content
