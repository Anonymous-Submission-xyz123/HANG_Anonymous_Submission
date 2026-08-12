# Natural language intent:
# Define a PowerShell script in a variable and convert it to Unicode-encoded bytes.

$a = "Write-Host 'Hello World!'"; $b = [System.Text.Encoding]::Unicode.GetBytes($a)
