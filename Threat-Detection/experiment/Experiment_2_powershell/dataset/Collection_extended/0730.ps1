# Natural language intent:
# Listing Running Processes with Details, Lists all currently running processes on the system, sorted by CPU usage, and includes process names, IDs, and CPU time.

Get-Process | Select-Object -Property ProcessName, Id, CPU | Sort-Object -Property CPU -Descending
