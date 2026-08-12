# Natural language intent:
# Invoke a WMI command to create a process on a remote node.

wmic /node:${node} process call create "rundll32.exe ${dll_to_execute} ${function_to_execute}"
