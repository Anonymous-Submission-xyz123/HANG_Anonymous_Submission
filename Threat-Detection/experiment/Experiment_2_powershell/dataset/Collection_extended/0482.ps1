# Natural language intent:
# Start a hidden PowerShell process and load a specific assembly.

$process = Start-Process -FilePath powershell.exe -ArgumentList '-nop', '-w', 'hidden', '-e', '[System.Reflection.Assembly]::LoadWithPartialName("AssemblyName")'
