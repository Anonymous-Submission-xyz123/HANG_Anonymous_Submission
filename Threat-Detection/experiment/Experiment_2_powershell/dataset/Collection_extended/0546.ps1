# Natural language intent:
# Start a process (WebBrowserPassView), sleep for 3 seconds, and then stop the process.

Start-Process ${WebBrowserPassViewPath} ; Start-Sleep -Second 3 ; Stop-Process -Name "WebBrowserPassView"
