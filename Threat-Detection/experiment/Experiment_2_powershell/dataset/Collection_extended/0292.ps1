# Natural language intent:
# Execute a command using cmd.exe to perform asreproast with specific output file settings.

cmd.exe /c "${local_folder}\${local_executable}" asreproast /outfile:"${local_folder}\${out_file}"
