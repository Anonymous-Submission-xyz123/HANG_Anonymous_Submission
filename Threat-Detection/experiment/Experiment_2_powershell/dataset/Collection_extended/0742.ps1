# Natural language intent:
# Accessing Event Logs for Anomalies, Searches the Security event log for entries where the entry type is `FailureAudit', which can indicate securityrelated anomalies.

Get-EventLog -LogName Security | Where-Object {$_.EntryType -eq 'FailureAudit'}
