# Natural language intent:
# Since the SYSVOL network shares are accessible to any authenticated domain user, we can easily identify if there are any stored credentials using the following command:

Push-Location \\\\example.com\sysvol;gci * -Include *.xml,*.txt,*.bat,*.ps1,*.psm,*.psd -Recurse -EA SilentlyContinue | select-string password;Pop-Location
