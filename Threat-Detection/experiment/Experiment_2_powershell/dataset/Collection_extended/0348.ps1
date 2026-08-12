# Natural language intent:
# Invoke REST method to retrieve metadata and convert it to JSON, then save it to an output file.

Invoke-RestMethod -Headers @{"Metadata"="true"} -Method GET -Uri "http://169.254.169.254/metadata/instance?api-version=2021-02-01" | ConvertTo-Json -Depth 64 > ${output_file}
