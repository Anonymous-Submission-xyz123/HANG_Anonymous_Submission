# Natural language intent:
# Copy a file from a remote location to the local temporary folder.

copy-item -Path "\${remote}\C$${ShareFile}" -Destination "$Env:TEMP${LocalFile}"
