# Natural language intent:
# Create a new Hyper-V virtual machine named ${vm_name} with Generation 2, disable Secure Boot in its firmware settings, and start the virtual machine.

$VM = "${vm_name}" ; New-VM -Name $VM -Generation 2 ; Set-VMFirmware $VM -EnableSecureBoot Off ; Start-VM $VM
