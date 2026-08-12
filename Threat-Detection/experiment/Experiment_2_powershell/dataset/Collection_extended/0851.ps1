# Natural language intent:
# List installed antivirus (AV) products, Here's a simple PowerShell command to query Security Center and identify all installed Antivirus products on this computer:

Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct
