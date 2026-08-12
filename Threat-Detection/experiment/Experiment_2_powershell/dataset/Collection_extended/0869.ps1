# Natural language intent:
# Extracting Saved RDP Credentials, Lists and deletes saved Remote Desktop Protocol (RDP) credentials, which can be used to access remote systems.

cmdkey /list | Select-String 'Target: TERMSRV' | ForEach-Object { cmdkey /delete:($_ -split ' ')[-1] }
