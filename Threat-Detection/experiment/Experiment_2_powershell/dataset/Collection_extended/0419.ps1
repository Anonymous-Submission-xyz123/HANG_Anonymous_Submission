# Natural language intent:
# Copy a file, start a process with it, retrieve the process ID, and stop the process using PowerShell.

copy ${input_file} ${output_file} ; $my_technique = (Start-Process -PassThru -FilePath ${output_file}).Id ; Stop-Process -ID $technique
