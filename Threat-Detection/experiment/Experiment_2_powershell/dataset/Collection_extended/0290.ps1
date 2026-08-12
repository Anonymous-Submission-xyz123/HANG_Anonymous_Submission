# Natural language intent:
# Compress the specified input files into a new archive at the specified destination with forced compression.

Compress-Archive -Path ${input_file} -DestinationPath ${output_file} -Force
