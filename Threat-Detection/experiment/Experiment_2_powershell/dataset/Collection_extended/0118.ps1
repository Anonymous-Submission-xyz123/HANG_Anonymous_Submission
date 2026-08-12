# Natural language intent:
# Start a foreground BITS transfer from a remote source to a local destination.

Start-BitsTransfer -Priority foreground -Source ${remote_file} -Destination ${local_file}
