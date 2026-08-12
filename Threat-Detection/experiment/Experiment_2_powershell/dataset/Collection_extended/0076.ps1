# Natural language intent:
# Perform DNS MX record lookup for a specified domain and filter the output for mail-related information.

(nslookup -querytype=mx ${target.org.domain}. | Select-String -pattern 'mail' | Out-String).Trim()
