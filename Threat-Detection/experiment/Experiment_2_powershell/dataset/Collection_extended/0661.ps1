# Natural language intent:
# Invoke a command to start PowerShell via cmd, launch a Tor executable, sleep for 60 seconds, and stop the Tor process.

invoke-expression 'cmd /c start powershell -Command {cmd /c ${TorExe}}' ; sleep -s 60 ; stop-process -name "tor" | out-null
