# Natural language intent:
# Set MAC address from command-line, Sometimes it can be useful to set MAC address on a network interface and with PowerShell we can easily do it without using any 3rd party utility:

Set-NetAdapter -Name "Ethernet0" -MacAddress "00-01-18-57-1B-0D"
