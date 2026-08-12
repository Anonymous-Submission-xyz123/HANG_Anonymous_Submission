# Natural language intent:
# Start a process and then launch a new process under a specific parent with specified parameters.

Start-Process -FilePath ${parent_name} -PassThru | Start-ATHProcessUnderSpecificParent -FilePath ${file_path} -CommandLine '${command_line}'
