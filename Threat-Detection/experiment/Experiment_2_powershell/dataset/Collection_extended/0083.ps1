# Natural language intent:
# Execute a DLL through WMI on a remote node using rundll32.

wmic /node:${node} process call create "rundll32.exe ${your_dll} ${YourFuctionToExecute}"
