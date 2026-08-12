# Natural language intent:
# Run a command using cmd to print a file with WordPad multiple times.

cmd /c "for /l %x in (1,1,${max_to_print}) do start wordpad.exe /p ${file_to_print}" | out-null
