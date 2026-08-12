# Natural language intent:
# Here's a quick one-liner for checking whether we are running elevated PowerShell session with Administrator privileges:

If (([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) { echo "yes"; } else { echo "no"; }
