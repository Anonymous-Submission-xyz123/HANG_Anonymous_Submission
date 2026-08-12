# Natural language intent:
# Retrieve LAPS passwords from a domain controller

Get-LAPSPasswords -DomainController 192.168.1.1 -Credential demo.com\administrator | Export-Csv c:	emp\output.csv -NoTypeInformation
