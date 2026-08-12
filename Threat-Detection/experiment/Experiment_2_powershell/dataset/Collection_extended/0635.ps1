# Natural language intent:
# Import a PowerShell module and use timestomp to modify timestamps for a file.

import-module ${path}\timestomp.ps1 ; timestomp -dest "${path}\kxwn.lock"
