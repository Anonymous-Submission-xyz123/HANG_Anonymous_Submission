# Natural language intent:
# Using PowerShell to Access WMI for Stealth, Leverages WMI (Windows Management Instrumentation) to execute system queries, which can be less conspicuous than direct PowerShell commands.

$query = 'SELECT * FROM Win32_Process'; Get-WmiObject -Query $query
