# Natural language intent:
# Using the Get-WinEvent cmdlet to query the Security log for events with Event ID 4769. The command filters the events based on various conditions in the event message. Specifically, it filters out events where the service account is 'krbtgt,' the account name ends with '$', the account name does not contain '$@', the failure status is '0x0,' and the substatus is '0x17'.

Get-WinEvent -FilterHashtable @{Logname='Security';ID=4769} -MaxEvents 1000 | ?{$_.Message.split("`n")[8] -ne 'krbtgt' -and $_.Message.split("`n")[8] -ne '*$' -and $_.Message.split("`n")[3] -notlike '*$@*' -and $_.Message.split("`n")[18] -like '*0x0*' -and $_.Message.split("`n")[17] -like "*0x17*"} | select ExpandProperty message
