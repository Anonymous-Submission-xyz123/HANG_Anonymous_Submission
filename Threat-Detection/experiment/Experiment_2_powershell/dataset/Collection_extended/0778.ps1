# Natural language intent:
# Search registry for auto-logon credentials, Windows systems can be configured to auto login upon boot, which is for example used on POS (point of sale) systems. Typically, this is configured by storing the username and password in a specific Winlogon registry location, in clear text.The following command will get the auto-login credentials from the registry:

gp 'HKLM:\SOFTWARE\Microsoft\Windows NT\Currentversion\Winlogon' | select "Default*"
