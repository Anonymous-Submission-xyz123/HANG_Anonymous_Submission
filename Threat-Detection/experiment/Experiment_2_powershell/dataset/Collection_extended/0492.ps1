# Natural language intent:
# Compress the contents of a directory into an archive file.

dir ${input_file} -Recurse | Compress-Archive -DestinationPath ${output_file}
