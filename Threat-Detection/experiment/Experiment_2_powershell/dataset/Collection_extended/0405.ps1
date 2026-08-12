# Natural language intent:
# Disable HTTP logging for a specified website in IIS using PowerShell.

set-WebConfigurationProperty -PSPath "IIS:\Sites\${website_name}\" -filter "system.webServer/httpLogging" -name dontLog -value $true
