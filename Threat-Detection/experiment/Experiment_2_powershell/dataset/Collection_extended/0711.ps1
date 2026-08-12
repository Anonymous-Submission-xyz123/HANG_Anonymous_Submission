# Natural language intent:
# You can use Set-DCShadowPermissions to give these privileges to an unprivileged user (notice that this will leave some logs). This is much more restrictive than having DA privileges.

Set-DCShadowPermissions -FakeDC mcorp-student1 SAMAccountName root1user -Username student1 -Verbose
