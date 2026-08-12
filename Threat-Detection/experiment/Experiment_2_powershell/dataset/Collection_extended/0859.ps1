# Natural language intent:
# Finding Windows Servers on the domain Using PowerShell, get a list of Windows boxes. Servers are usually priority, so lets focus there:

Get-ADComputer -Filter {(OperatingSystem -like "*windows*server*") -and (OperatingSystem -notlike "2016") -and (Enabled -eq "True")} -Properties * | select Name | ft -HideTableHeaders > servers.txt
