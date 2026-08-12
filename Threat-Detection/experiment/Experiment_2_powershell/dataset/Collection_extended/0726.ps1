# Natural language intent:
# Find unquoted service paths, This can lead to privilege escalation in case the executable path also contains spaces and we have write permissions to any of the folders in the path., The following PowerShell command will print out services whose executable path is not enclosed within quotes ('):

gwmi -class Win32_Service -Property Name, DisplayName, PathName, StartMode | Where {$_.StartMode -eq "Auto" -and $_.PathName -notlike "C:\Windows*" -and $_.PathName -notlike '"*'} | select PathName,DisplayName,Name
