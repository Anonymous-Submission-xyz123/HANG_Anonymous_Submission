# Natural language intent:
# Configure IIS logging settings

C:\Windows\System32\inetsrv\appcmd.exe set config "${website_name}" /section:httplogging /dontLog:true
