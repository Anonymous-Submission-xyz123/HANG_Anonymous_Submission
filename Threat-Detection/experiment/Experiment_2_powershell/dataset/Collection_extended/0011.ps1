# Natural language intent:
# Compress files from the specified directory into an archive.

dir ${InputFile} -Recurse | Compress-Archive -DestinationPath ${OutputFile}
