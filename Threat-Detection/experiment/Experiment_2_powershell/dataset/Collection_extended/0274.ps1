# Natural language intent:
# Execute a command using cmd.exe to perform asreproast with specific output file settings.

cmd.exe /c "${LocalFolder}\${local_executable}" asreproast /outfile:"${LocalFolder}\${out_file}"
