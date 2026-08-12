# Natural language intent:
# Create a new WebClient object and configure proxy settings using the system's web proxy.

$Invoke = New-Object System.Net.WebClient; $Invoke.Proxy = [System.Net.WebRequest]::GetSystemWebProxy(); $Invoke.Proxy.Credentials = [System.Net.CredentialCache]
