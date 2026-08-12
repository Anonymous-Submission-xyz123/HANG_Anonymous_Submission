# Natural language intent:
# Create a notepad process, inject context, wait for 5 seconds, and then stop the notepad process.

$notepad = Start-Process notepad -passthru ; Start-Process $PathToAtomicsFolder\T1055.003\bin\InjectContext.exe ; Start-Sleep -Seconds 5 ; Stop-Process $notepad.id
