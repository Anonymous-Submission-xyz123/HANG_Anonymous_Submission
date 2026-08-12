# Natural language intent:
# Check for virtualization environment and print a message if detected using PowerShell.

$error.clear() ; Get-WmiObject -Query "SELECT * FROM MSAcpi_ThermalZoneTemperature" -ErrorAction SilentlyContinue ; if($error) {echo "Virtualization Environment detected"}
