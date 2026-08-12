# Natural language intent:
# Run a command using cmd to control Windows Defender settings.

cmd /c ${DefenderControlExe} /D ${DefenderID} | Out-Null
