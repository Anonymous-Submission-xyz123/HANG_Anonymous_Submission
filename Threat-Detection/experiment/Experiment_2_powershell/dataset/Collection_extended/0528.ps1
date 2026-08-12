# Natural language intent:
# Start a process (Web browser passview) and stop it after 5 seconds.

Start-Process ${Web_browser_passview_Path} ; Start-Sleep -Second 5 ; Stop-Process -Name "WebBrowserPassView"
