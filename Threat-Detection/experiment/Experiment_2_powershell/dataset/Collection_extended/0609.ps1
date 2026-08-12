# Natural language intent:
# Configure IIS logging settings

C:\Windows\System32\inetsrv\appcmd.exe set config "${WebsiteName}" /section:httplogging /dontLog:true
